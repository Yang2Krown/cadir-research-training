#!/usr/bin/env python3
"""Build an HSC small-package skeleton or a review-gated ZIP of explicit artifacts.

The script never deserializes scientific data or reads expression values. In
assemble mode it only copies manifest-listed small files, hashes file bytes,
and writes an external-object index. All RDS files remain external.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile

SMALL_EXTENSIONS = {
    "", ".csv", ".json", ".log", ".md", ".pdf", ".png", ".py", ".r",
    ".sh", ".timing", ".tsv", ".txt", ".typescript", ".yml", ".yaml",
}
ALWAYS_EXTERNAL = {".rds", ".rda", ".rdata", ".qs", ".h5", ".h5ad", ".hdf5", ".loom", ".mtx", ".gz"}
TERMINAL_STATES = {"success", "failed", "timeout", "oom", "error", "completed_with_failure"}
REVIEW_PASS_STATES = {"PASS", "PASS_LIMITED", "PASS_LIMITED_RESULT_REVIEW", "PASS_LIMITED_RESULT_ACCEPTANCE"}


class PackageError(Exception):
    pass


def fail(message: str) -> None:
    raise PackageError(message)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def relative_path(value: str, label: str) -> Path:
    if not value or "[FILL" in value or value.startswith("["):
        fail(f"{label} is blank or still a placeholder: {value!r}")
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        fail(f"{label} must be a safe path relative to its named root: {value}")
    return rel


def path_under(root: Path, value: str, label: str) -> Path:
    root = root.expanduser().resolve(strict=True)
    raw = root / relative_path(value, label)
    if raw.is_symlink():
        fail(f"{label} may not be a symbolic link: {raw}")
    candidate = raw.resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError:
        fail(f"{label} escapes its declared root: {value}")
    if not candidate.is_file() or candidate.is_symlink():
        fail(f"{label} is not a regular file: {candidate}")
    return candidate


def source_bytes(source: dict, roots: dict[str, Path]) -> tuple[bytes | None, Path | None]:
    kind = source.get("type")
    root_name = source.get("root")
    if root_name not in roots:
        fail(f"Missing explicit source root {root_name!r}")
    rel = relative_path(source.get("path", ""), "source.path")
    root = roots[root_name]
    if kind == "file":
        return None, path_under(root, str(rel), "source.path")
    if kind == "git":
        commit = source.get("commit", "")
        git_path = str(rel).replace(os.sep, "/")
        if not commit or "[FILL" in commit:
            fail("Git source commit is missing or a placeholder")
        check = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True)
        if check.returncode:
            fail(f"Git commit is unavailable locally: {commit}")
        proc = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{git_path}"], capture_output=True)
        if proc.returncode:
            fail(f"Git source path is unavailable: {commit}:{git_path}")
        return proc.stdout, None
    fail(f"Unsupported source type: {kind!r}")


def git_tree_files(root: Path, commit: str, prefix: str) -> list[tuple[str, str, int]]:
    """Return safe Git tree entries as (relative path, blob OID, byte size)."""
    root = root.expanduser().resolve(strict=True)
    if not commit or "[FILL" in commit:
        fail("Git-tree commit is missing or a placeholder")
    rel_prefix = relative_path(prefix, "source.path").as_posix().rstrip("/")
    check = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True)
    if check.returncode:
        fail(f"Git-tree commit is unavailable locally: {commit}")
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", "--long", "-z", commit, "--", rel_prefix],
        capture_output=True,
    )
    if proc.returncode:
        fail(f"Could not list Git tree: {commit}:{rel_prefix}")
    rows: list[tuple[str, str, int]] = []
    for record in proc.stdout.split(b"\0"):
        if not record:
            continue
        try:
            meta, raw_path = record.split(b"\t", 1)
            mode, object_type, oid, size_text = meta.decode("ascii").split()
            path = raw_path.decode("utf-8")
            size = int(size_text)
        except (ValueError, UnicodeDecodeError):
            fail("Malformed Git-tree listing")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            fail(f"Non-regular file in packaged Git tree: {path}")
        marker = rel_prefix + "/"
        if not path.startswith(marker):
            fail(f"Git-tree path escaped its declared prefix: {path}")
        relative = path[len(marker):]
        safe = relative_path(relative, "Git-tree member")
        rows.append((safe.as_posix(), oid, size))
    if not rows:
        fail(f"Git tree is empty: {commit}:{rel_prefix}")
    return rows


def git_blob_bytes(root: Path, oid: str, expected_size: int, label: str) -> bytes:
    proc = subprocess.run(["git", "-C", str(root), "cat-file", "blob", oid], capture_output=True)
    if proc.returncode:
        fail(f"Could not read packaged Git blob for {label}")
    if len(proc.stdout) != expected_size:
        fail(f"Git blob size mismatch for {label}")
    return proc.stdout


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_zip(zip_path: Path, package_dir: Path, package_root_name: str) -> str:
    """Verify ZIP CRCs and SHA-256 for every stored file against the package tree."""
    expected = {
        p.relative_to(package_dir).as_posix(): sha256_path(p)
        for p in package_dir.rglob("*") if p.is_file()
    }
    with zipfile.ZipFile(zip_path, "r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            fail(f"ZIP CRC verification failed for {bad_member}")
        names = set(archive.namelist())
        prefix = package_root_name + "/"
        archive_files = {name[len(prefix):] for name in names if name.startswith(prefix) and not name.endswith("/")}
        if archive_files != set(expected):
            fail(f"ZIP member list differs from package tree: missing={sorted(set(expected)-archive_files)}, extra={sorted(archive_files-set(expected))}")
        rds_members = sorted(name for name in archive_files if Path(name).suffix.lower() == ".rds")
        if rds_members:
            fail(f"RDS files must remain external to the ZIP: {rds_members}")
        for relative, expected_sha in expected.items():
            member = prefix + relative
            h = hashlib.sha256()
            with archive.open(member, "r") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(block)
            if h.hexdigest() != expected_sha:
                fail(f"ZIP SHA-256 verification failed for {relative}")
    return sha256_path(zip_path)


def check_source_hash(expected: str | None, actual: str, label: str) -> None:
    if expected and expected != actual:
        fail(f"SHA-256 mismatch for {label}: expected {expected}, got {actual}")


def validate_release(manifest: dict, results_root: Path) -> None:
    if manifest.get("release_status") != "READY_AFTER_INDEPENDENT_RESULT_REVIEW":
        fail("Manifest is not marked READY_AFTER_INDEPENDENT_RESULT_REVIEW")
    if manifest.get("ready_to_assemble") is not True or manifest.get("run_matrix_complete") is not True:
        fail("The full run matrix and assembly gate are not marked complete")
    declared_root = manifest.get("roots", {}).get("results", "")
    if not declared_root or "[FILL" in declared_root:
        fail("Manifest must declare the actual results root")
    if Path(declared_root).expanduser().resolve() != results_root.resolve():
        fail("--results-root does not match the manifest's frozen results root")
    review = manifest.get("independent_results_review", {})
    if review.get("status") not in REVIEW_PASS_STATES:
        fail("Independent result-review status is not a passing state")
    if not review.get("report_path") or "[FILL" in review["report_path"] or not review.get("report_sha256"):
        fail("Independent result-review report path and SHA-256 are required")
    report_path = Path(review["report_path"]).expanduser().resolve(strict=True)
    if not report_path.is_file() or sha256_path(report_path) != review["report_sha256"]:
        fail("Independent result-review report is missing or its SHA-256 does not match")
    decision_path_value = review.get("decision_path")
    decision_sha = review.get("decision_sha256")
    if decision_path_value or decision_sha:
        if not decision_path_value or not decision_sha:
            fail("Both independent decision path and SHA-256 are required when either is supplied")
        decision_path = Path(decision_path_value).expanduser().resolve(strict=True)
        if sha256_path(decision_path) != decision_sha:
            fail("Independent result-review decision SHA-256 does not match")
        with decision_path.open(encoding="utf-8") as stream:
            decision = json.load(stream)
        if decision.get("decision") != review.get("status"):
            fail("Independent result-review decision does not match the manifest status")
        if decision.get("result_commit") != manifest.get("bindings", {}).get("results_archive_commit"):
            fail("Independent result-review decision is not bound to the frozen results archive commit")
        if decision.get("source_commit") != manifest.get("bindings", {}).get("implementation_commit"):
            fail("Independent result-review decision is not bound to the admitted implementation commit")
    text_review_path_value = review.get("text_review_path")
    text_review_sha = review.get("text_review_sha256")
    if text_review_path_value or text_review_sha:
        if not text_review_path_value or not text_review_sha:
            fail("Both limited text-review path and SHA-256 are required when either is supplied")
        text_review_path = Path(text_review_path_value).expanduser().resolve(strict=True)
        if sha256_path(text_review_path) != text_review_sha:
            fail("Limited text-review SHA-256 does not match")
        with text_review_path.open(encoding="utf-8") as stream:
            text_review = json.load(stream)
        if text_review.get("status") != review.get("text_review_status"):
            fail("Limited text-review status does not match the manifest")

    matrix = manifest.get("expected_run_matrix", {})
    methods = matrix.get("methods", [])
    seeds = matrix.get("seeds", [])
    outcomes = matrix.get("core_terminal_outcomes", [])
    expected = {(method, seed) for method in methods for seed in seeds}
    observed = set()
    for row in outcomes:
        pair = (row.get("method"), row.get("seed"))
        if pair not in expected or row.get("status") not in TERMINAL_STATES or row.get("final") is not True:
            fail(f"Invalid or non-terminal core run receipt row: {row}")
        if pair in observed:
            fail(f"Duplicate final core outcome for {pair}")
        observed.add(pair)
    if observed != expected:
        fail(f"Core run matrix incomplete: missing {sorted(expected - observed)}")

    expected_diagnostics = matrix.get("diagnostics_expected")
    diagnostics = matrix.get("diagnostic_terminal_receipts", [])
    if not isinstance(expected_diagnostics, int) or len(diagnostics) != expected_diagnostics:
        fail("Diagnostic terminal receipt count does not match the declared count")
    for row in diagnostics:
        if row.get("status") not in TERMINAL_STATES or not row.get("id"):
            fail(f"Invalid or non-terminal diagnostic receipt row: {row}")


def make_skeleton(output: Path, template_path: Path) -> None:
    if output.exists():
        fail(f"Output already exists; refusing to overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        for directory in [
            "provenance/stage1", "provenance/source", "provenance/design-review",
            "results/tables", "results/runs", "results/captions", "figures",
            "operations/timing", "reviews/result-review", "status", "backup", "external",
        ]:
            (temp / directory).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(template_path, temp / "package-manifest.template.json")
        (temp / "README_NOT_FINAL.md").write_text(
            "This is only a directory skeleton. No result files were copied.\n"
            "Replace the manifest placeholders and pass the run/review gates before assembly.\n",
            encoding="utf-8",
        )
        os.replace(temp, output)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def add_external_row(rows: list[dict], item_id: str, path: Path, sha: str, sha_source: str, reason: str) -> None:
    rows.append({
        "artifact_id": item_id,
        "absolute_path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha,
        "sha_source": sha_source,
        "reason": reason,
        "git_archive_path": "",
    })


def assemble(manifest_path: Path, output: Path, zip_path: Path | None, results_root: Path, root_overrides: dict[str, Path]) -> None:
    if output.exists():
        fail(f"Output already exists; refusing to overwrite: {output}")
    if zip_path and zip_path.exists():
        fail(f"ZIP output already exists; refusing to overwrite: {zip_path}")
    with manifest_path.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    results_root = results_root.expanduser().resolve(strict=True)
    validate_release(manifest, results_root)

    roots = {}
    for name, raw_path in manifest.get("roots", {}).items():
        if raw_path and "[FILL" not in raw_path:
            roots[name] = Path(raw_path).expanduser().resolve(strict=True)
    roots.update({name: path.expanduser().resolve(strict=True) for name, path in root_overrides.items() if path})
    roots["results"] = results_root
    roots.setdefault("workspace", Path("/workspace").resolve(strict=True))

    required = set(manifest.get("required_artifact_ids", []))
    artifacts = manifest.get("artifacts", [])
    by_id = {item.get("id"): item for item in artifacts}
    missing_ids = sorted(required - set(by_id))
    if missing_ids:
        fail(f"Required artifact IDs missing from manifest: {missing_ids}")
    for artifact_id in required:
        item = by_id[artifact_id]
        if item.get("state") != "ready" or item.get("required") is not True:
            fail(f"Required artifact is not ready: {artifact_id}")

    limits = manifest.get("limits", {})
    max_file = int(limits.get("small_file_max_bytes", 50_000_000))
    max_total = int(limits.get("small_package_max_bytes", 250_000_000))
    allowed = {suffix.lower() for suffix in limits.get("allowed_small_extensions", SMALL_EXTENSIONS)}
    prepared = []
    total_bytes = 0
    for item in artifacts:
        if item.get("state") != "ready":
            if item.get("required"):
                fail(f"Required artifact still pending: {item.get('id')}")
            continue
        if item.get("file_class") != "small":
            fail(f"Only explicitly small files may be copied into the package: {item.get('id')}")
        package_rel = relative_path(item.get("package_path", ""), "package_path")
        source = item.get("source", {})
        if source.get("type") == "git_tree":
            root_name = source.get("root")
            if root_name not in roots:
                fail(f"Missing Git-tree source root {root_name!r}")
            git_root = roots[root_name]
            entries = git_tree_files(git_root, source.get("commit", ""), source.get("path", ""))
            excluded_rds = 0
            included_count = 0
            included_bytes = 0
            for relative, oid, tree_size in entries:
                suffix = Path(relative).suffix.lower()
                if suffix in ALWAYS_EXTERNAL:
                    if suffix == ".rds":
                        excluded_rds += 1
                    continue
                destination_rel = package_rel / relative_path(relative, "Git-tree member")
                if destination_rel.suffix.lower() not in allowed:
                    fail(f"Git-tree file extension is not allowlisted: {destination_rel}")
                if tree_size > max_file:
                    fail(f"Git-tree file exceeds the per-file cap: {destination_rel} ({tree_size} bytes)")
                data = git_blob_bytes(git_root, oid, tree_size, relative)
                digest = hash_bytes(data)
                expected_member_sha = source.get("expected_file_sha256", {}).get(relative)
                check_source_hash(expected_member_sha, digest, f"{item.get('id')}:{relative}")
                total_bytes += tree_size
                included_count += 1
                included_bytes += tree_size
                if total_bytes > max_total:
                    fail(f"Small-package payload exceeds the total size cap ({total_bytes} bytes)")
                prepared.append((item, data, None, tree_size, digest, destination_rel.as_posix()))
            expected_excluded = item.get("expected_excluded_rds")
            if expected_excluded is not None and excluded_rds != int(expected_excluded):
                fail(f"Excluded RDS count mismatch for {item.get('id')}: expected {expected_excluded}, found {excluded_rds}")
            expected_included = item.get("expected_included_files")
            if expected_included is not None and included_count != int(expected_included):
                fail(f"Included Git-tree file count mismatch for {item.get('id')}: expected {expected_included}, found {included_count}")
            expected_bytes = item.get("expected_included_bytes")
            if expected_bytes is not None and included_bytes != int(expected_bytes):
                fail(f"Included Git-tree byte count mismatch for {item.get('id')}: expected {expected_bytes}, found {included_bytes}")
            continue

        source_suffix = Path(source.get("path", "")).suffix.lower()
        if package_rel.suffix.lower() in ALWAYS_EXTERNAL or source_suffix in ALWAYS_EXTERNAL:
            fail(f"RDS/raw binary objects may not enter the small package: {item.get('id')}")
        if package_rel.suffix.lower() not in allowed:
            fail(f"File extension is not allowlisted: {package_rel}")
        data, source_path = source_bytes(source, roots)
        if data is not None:
            size = len(data)
            digest = hash_bytes(data)
        else:
            size = source_path.stat().st_size
            digest = sha256_path(source_path)
        if size > max_file:
            fail(f"Small-package file exceeds the per-file cap: {item.get('id')} ({size} bytes)")
        check_source_hash(source.get("expected_sha256"), digest, str(item.get("id")))
        total_bytes += size
        if total_bytes > max_total:
            fail(f"Small-package payload exceeds the total size cap ({total_bytes} bytes)")
        prepared.append((item, data, source_path, size, digest, str(package_rel)))

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    external_rows = []
    copied_records = []
    try:
        for directory in [
            "provenance/stage1", "provenance/source", "provenance/design-review",
            "results/tables", "results/runs", "results/captions", "figures",
            "operations/timing", "reviews/result-review", "status", "backup", "external",
        ]:
            (temp / directory).mkdir(parents=True, exist_ok=True)
        for item, data, source_path, size, digest, package_rel in prepared:
            destination = temp / package_rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            if data is not None:
                destination.write_bytes(data)
            else:
                shutil.copyfile(source_path, destination)
            copied_records.append({"id": item["id"], "path": package_rel, "bytes": size, "sha256": digest})

        for item in manifest.get("external_objects", []):
            root_name = item.get("source_root")
            if root_name not in roots:
                fail(f"Missing external-object source root: {root_name}")
            path = path_under(roots[root_name], item.get("source_path", ""), item.get("id", "external object"))
            size = path.stat().st_size
            expected_bytes = item.get("expected_bytes")
            if expected_bytes is not None and size != int(expected_bytes):
                fail(f"External object size mismatch: {item.get('id')}")
            sha = item.get("sha256")
            sha_source = item.get("sha_source", "computed after run completion")
            if not sha:
                sha = sha256_path(path)
                sha_source = "computed by this archive script from file bytes; not deserialized"
            add_external_row(external_rows, item.get("id", "external"), path, sha, sha_source, item.get("reason", "external object"))
            if item.get("archive_path"):
                external_rows[-1]["git_archive_path"] = item["archive_path"]

        external_paths = [row["absolute_path"] for row in external_rows]
        if len(external_paths) != len(set(external_paths)):
            fail("Duplicate absolute paths in external-object manifest")

        # Do not re-hash large result objects here. The exact paths, byte counts,
        # and SHA-256 values come from the committed large-object and archive-copy
        # manifests. This pass checks path coverage and byte counts only.
        declared_external_paths = {row["absolute_path"] for row in external_rows}
        for path in sorted(results_root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            size = path.stat().st_size
            if path.suffix.lower() in ALWAYS_EXTERNAL or size > max_file:
                if str(path.resolve()) not in declared_external_paths:
                    fail(f"Large/RDS result object is missing from the committed external-object manifest: {path}")

        external_path = temp / "external-objects.tsv"
        with external_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["artifact_id", "absolute_path", "bytes", "sha256", "sha_source", "reason", "git_archive_path"], delimiter="\t")
            writer.writeheader()
            writer.writerows(external_rows)

        final_manifest = {
            "package_id": manifest["package_id"],
            "release_status": manifest["release_status"],
            "results_root": str(results_root),
            "implementation_commit": manifest["bindings"]["implementation_commit"],
            "results_archive_commit": manifest["bindings"].get("results_archive_commit"),
            "results_archive_path": manifest["bindings"].get("results_archive_path"),
            "design_review_commit": manifest["bindings"]["design_review_commit"],
            "admission_sha256": manifest["bindings"]["admission_sha256"],
            "independent_results_review": manifest["independent_results_review"],
            "run_matrix": manifest["expected_run_matrix"],
            "external_object_count": len(external_rows),
            "result_tree_non_rds_file_count": sum(1 for row in copied_records if row["id"] == "frozen-result-tree"),
            "all_rds_excluded_from_zip": True,
            "included_files": copied_records,
            "external_objects_index": "external-objects.tsv",
            "raw_data_backup_status": manifest.get("raw_data_backup_status", "not verified unless explicitly documented"),
        }
        (temp / "package-manifest.json").write_text(json.dumps(final_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (temp / "README_zh.md").write_text(
            "# HSC 结果小包\n\n"
            f"准入实现提交：{manifest['bindings']['implementation_commit']}。\n\n"
            f"独立设计审查提交：[GitHub commit](https://github.com/Yang2Krown/cadir-research-training/commit/{manifest['bindings']['design_review_commit']})；阶段一和 C04 范围说明位于包内 `results/design-admission/`。\n\n"
            f"结果归档提交：[GitHub commit](https://github.com/Yang2Krown/cadir-research-training/commit/{manifest['bindings']['results_archive_commit']})；仓库路径 `{manifest['bindings']['results_archive_path']}` 对应包内 `results/`。\n\n"
            f"独立结果复验：[签字提交](https://github.com/Yang2Krown/cadir-research-training/commit/{manifest['independent_results_review']['review_commit']})，decision 为 `{manifest['independent_results_review']['status']}`；完整报告和复验记录位于包内 `reviews/result-review/`。\n\n"
            "结果树中的实际结果报告、展示状态和终端记录保留为 091a8a4 提交时的原样快照；其中‘待复验’是当时状态，之后由上述已签 reviewer decision 与文稿记录取代。签署报告和历史快照均未改写。\n\n"
            "中文结果段落和 PPT 讲稿位于包内 `documents/`。来源获取记录说明原始输入为本会话重新获取，不是缺失历史原件的恢复。ZIP 只放入结果树中的非 RDS 文件；全部 RDS、raw 和共同预处理对象不进入 ZIP，精确外置路径、字节数和 SHA-256 见 external-objects.tsv。Mac 看板未同步，用户本机完整备份尚未验证；此小包不替代完整原始数据备份。\n",
            encoding="utf-8",
        )
        checksum_file = temp / "SHA256SUMS.txt"
        with checksum_file.open("w", encoding="utf-8") as stream:
            for path in sorted(p for p in temp.rglob("*") if p.is_file() and p != checksum_file):
                stream.write(f"{sha256_path(path)}  {path.relative_to(temp).as_posix()}\n")
        os.replace(temp, output)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise

    if zip_path:
        if zip_path.exists():
            fail(f"ZIP output already exists; refusing to overwrite: {zip_path}")
        if zip_path.resolve().is_relative_to(output.resolve()):
            fail("ZIP output must be outside the expanded package directory")
        checksum_path = Path(str(zip_path) + ".sha256")
        if checksum_path.exists():
            fail(f"ZIP SHA-256 sidecar already exists; refusing to overwrite: {checksum_path}")
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(p for p in output.rglob("*") if p.is_file()):
                archive.write(path, f"{manifest['package_id']}/{path.relative_to(output).as_posix()}")
        zip_sha = verify_zip(zip_path, output, manifest["package_id"])
        checksum_path.write_text(f"{zip_sha}  {zip_path.name}\n", encoding="utf-8")
        print(f"zip_crc=passed; member_sha256=passed; zip_sha256={zip_sha}; sidecar={checksum_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["skeleton", "assemble"], default="skeleton", help="Default is structure only; it does not read result files.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--results-root", type=Path, help="Required explicitly in assemble mode.")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--design-review-root", type=Path)
    parser.add_argument("--result-review-root", type=Path)
    parser.add_argument("--presentation-root", type=Path)
    parser.add_argument("--operations-root", type=Path)
    parser.add_argument("--backup-root", type=Path)
    parser.add_argument("--zip-path", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "skeleton":
            template = Path(__file__).resolve().parents[1] / "package_manifest.json"
            make_skeleton(args.output_dir.expanduser().resolve(), template)
            print(f"skeleton_created={args.output_dir.expanduser().resolve()}; no results read or copied")
            return 0
        if not args.manifest or not args.results_root:
            fail("assemble mode requires both --manifest and an explicit --results-root")
        overrides = {
            "repo": args.repo_root,
            "design_review": args.design_review_root,
            "result_review": args.result_review_root,
            "presentation": args.presentation_root,
            "operations": args.operations_root,
            "backup": args.backup_root,
        }
        assemble(args.manifest.expanduser().resolve(strict=True), args.output_dir.expanduser().resolve(), args.zip_path.expanduser().resolve() if args.zip_path else None, args.results_root, overrides)
        print(f"package_created={args.output_dir.expanduser().resolve()}")
        return 0
    except (PackageError, OSError, json.JSONDecodeError, csv.Error) as exc:
        print(f"archive_error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
