# CAdir cloud environment provenance

Research checkout: `/workspace/cadir-research-training`, left unchanged.
Environment and evidence: `/workspace/cadir-env` (outside research checkout).

Reference environment: https://github.com/VingronLab/CAdir_results at
`c15b49578bde38b42fd5db2c9830c10dd441ee4c`, `renv.lock` retained as
`upstream-renv.lock`. R 4.4.1, Bioconductor 3.19. This lock is reference
material, **not** restored wholesale. Its CAdir entry is an author's local
directory and does not identify a public commit. No license was found at
the reference repository's root LICENSE / LICENSE.md URLs; do not assume
a license for its research materials. Only the lock is retained.

Pinned package sources retained under `sources/`, including Git history,
DESCRIPTION and available license files:

| Package | Source | Commit | Declared license |
|---|---|---|---|
| CAdir 0.0.99 | https://github.com/VingronLab/CAdir | de74a008dfcd0d4fa4f7f93c57aa346892a8d935 | GPL >= 3; LICENSE.md retained |
| APL 1.9.1 | https://github.com/VingronLab/APL | d4d1f40d9ea9f1d9a95b224d45de843334cd617d | GPL >= 3; LICENSE.md retained |
| CAbiNet 0.99.2 | https://github.com/VingronLab/CAbiNet | 329c03298c5afc31a2b1fe3fa19b0fdd9f816d0b | GPL >= 3 in DESCRIPTION; no standalone license file found |
| ggsankey 0.0.99999 | https://github.com/davidsjoberg/ggsankey | b675d0d5144b1b5758d3b2b41e86ceee66a1e071 | MIT; LICENSE and LICENSE.md retained |

APL, CAbiNet and ggsankey commits match the author's reference lock.
CAdir is explicitly pinned separately because that lock gives no SHA.
Keep source and conda package license metadata with the environment.

CPU-only CA uses `python = FALSE`, the upstream default. Python torch,
CUDA, Python embedding and GPU paths are outside this environment's
validation scope. Reticulate automatic installation is disabled to avoid
unexpected downloads during package loading. Mandatory R imports remain
installed; no DESCRIPTION, lockfile or application source is edited.

This is an environment smoke check, not a paper reproduction. No course
datasets, formal experiments, benchmark algorithms or personal editor
configuration are part of setup. No `/Volumes` path is accessed.

Round 2: both Bioconductor 3.19 and CRAN indexes returned HTTP 200, with
TLS verification enabled. Conda R initially rejected the platform proxy
certificate; `activate.sh` now explicitly selects the host-managed trust
bundle `/etc/ssl/certs/ca-certificates.crt` using CURL_CA_BUNDLE and
SSL_CERT_FILE. No verification is disabled. Added matching zlib/expat
development packages and xorg-xorgproto so cairo's pkg-config dependency
graph resolves. All conda artifacts are recorded with SHA256 in the
updated explicit manifest. Index and compressed-package caches were
cleaned without removing installed packages. Aggregate disk figures use
`du` on the environment root, counting shared hardlinks once.

fgsea 1.30.0 initially failed because its C++11 request is incompatible
with BH 1.90.0-1's Boost.Math requirement (C++14 or later). The
package-specific `fgsea.Makevars` selects GNU C++17 through R's supported
CXX11STD build setting. Recompilation and installation succeeded; no
upstream package sources or dependency declarations were edited.
