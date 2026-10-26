#!/usr/bin/env python3
"""Independent real-input availability/provenance receipts; never makes fixture data.

Run prepare offline, acquire only with explicit executor network permission,
then seal offline. Each acquisition URL is attempted at most once in this run.
No A03 verifier is imported and no scientific computation is invoked.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

TARGET = 'b7ee2335dc25ffab3a60d1feab44272d6d5a45cb'
BASE = 'd853986e2e3a1cabc9f3f728f616e402432257ec'
CONTROL = '2d97dc8bd3cd70f2cedfa413c8b0446722aef843'
SOURCE = Path('/workspace/cadir-b7ee233-raw-independent-source-20261026')
REPORT = Path(__file__).resolve().parents[1]
RAW = Path('/workspace/cadir-b7ee233-raw-independent-data-20261026')
NAMES = ('counts.rds', 'coldata.rds', 'GSE81682_HTSeq_counts.txt.gz')
SOURCES = ('audit_inputs.R', 'metadata_identity.R', 'run_input_audit.py', 'test_metadata_identity.R')

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(block)
    return {'bytes': path.stat().st_size, 'sha256': sha.hexdigest()}

def run(label, argv, env=None, timeout=60):
    start, tick = now(), time.monotonic()
    try:
        result = subprocess.run(argv, capture_output=True, env=env, timeout=timeout)
        rc, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        rc, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
    except OSError as exc:
        rc, stdout, stderr = 127, b'', str(exc).encode()
    prefix = REPORT / 'logs' / label
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix('.stdout.log').write_bytes(stdout)
    prefix.with_suffix('.stderr.log').write_bytes(stderr)
    record = {'started_utc': start, 'ended_utc': now(), 'argv': argv,
              'exit_code': rc, 'elapsed_seconds': time.monotonic()-tick,
              'stdout_bytes': len(stdout), 'stderr_bytes': len(stderr)}
    save(prefix.with_suffix('.execution.json'), record)
    return record, stdout, stderr

def source_state():
    return {'observed_utc': now(), 'HEAD': subprocess.check_output(
        ['git','-C',str(SOURCE),'rev-parse','HEAD'], text=True).strip(),
        'status_porcelain': subprocess.check_output(
        ['git','-C',str(SOURCE),'status','--porcelain=v1','--untracked-files=all'], text=True),
        'files': {name: digest(SOURCE/'cases/nestorowa_hsc/scripts'/name) for name in SOURCES}}

def prepare():
    if (REPORT/'source_before.json').exists():
        raise SystemExit('refuse to overwrite preparation evidence')
    state = source_state()
    assert state['HEAD'] == TARGET and not state['status_porcelain']
    save(REPORT/'source_before.json', state)
    for name in SOURCES:
        dest = REPORT/'preserved-target-source'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE/'cases/nestorowa_hsc/scripts'/name, dest)
    manifest_path = SOURCE/'planning/new-dataset/2026-10-26/metadata-preparation/acquisition_manifest.json'
    shutil.copyfile(manifest_path, REPORT/'acquisition_manifest.target.json')
    save(REPORT/'fixed_refs.json', {'target': TARGET,'base': BASE,'control': CONTROL,
        'source_worktree': str(SOURCE),'raw_directory': str(RAW),
        'report_directory':str(REPORT),'formal_execution_permitted':False})
    # -L includes symlink targets; --hidden and --no-ignore avoid .gitignore omissions.
    cmd = ['rg','--files','--hidden','--no-ignore','-L','/workspace']
    for name in NAMES:
        cmd += ['-g', name]
    rec, out, err = run('real_file_search',cmd)
    candidates = [Path(x) for x in out.decode().splitlines() if x]
    verified = []
    manifest = json.loads(manifest_path.read_text())
    expected = {Path(a['path']).name:a for a in manifest['artifacts'] if Path(a['path']).name in NAMES}
    for path in candidates:
        if path.is_file():
            actual = digest(path)
            entry = expected[path.name]
            verified.append({'path':str(path), **actual,
                'matches_expected':actual['bytes']==entry['bytes'] and actual['sha256']==entry['sha256']})
    save(REPORT/'real_file_availability.before.json',{'observed_utc':now(),
        'search_command':cmd,'search_exit_code':rec['exit_code'],
        'search_stderr':err.decode(errors='replace'), 'candidates':verified,
        'priority_directories':{str(p):p.exists() for p in [
        Path('/workspace/nestorowa-hsc-data-audit'),
        Path('/workspace/nestorowa-metadata-preparation/reacquired-20261026')]}})
    save(REPORT/'environment/runtime_variables_presence.json', {key:bool(os.getenv(key)) for key in
        ['HTTP_PROXY','HTTPS_PROXY','NO_PROXY','SSL_CERT_FILE','CURL_CA_BUNDLE','REQUESTS_CA_BUNDLE','CODEX_PROXY_CERT']})
    shutil.copyfile('/etc/codex/network-policy.json',REPORT/'environment/network-policy.json')
    run('host_identity',['id'])
    run('host_uname',['uname','-a'])
    run('curl_version',['curl','--version'])
    docker_env = os.environ.copy()
    for key in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']:
        docker_env.pop(key,None)
    run('docker_info',['docker','--host=unix:///var/run/docker.sock','info'],docker_env)
    run('docker_image_inspect',['docker','--host=unix:///var/run/docker.sock','image','inspect',
        '--format','{{json .Id}}','cadir-r-ver:4.4.1-bioc3.19'],docker_env)
    renv = os.environ.copy()
    renv.update({'R_LIBS_USER':'/workspace/cadir-env/R-library','OMP_NUM_THREADS':'2',
        'OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2','RETICULATE_AUTOCONFIGURE':'FALSE'})
    rscript = '/workspace/cadir-env/skeleton_runtime/bin/Rscript'
    run('R_version',[rscript,'--version'],renv)
    run('R_actual_packages',[rscript,'--vanilla','-e',
        'cat(R.version.string,"\\n"); cat("R.home=",R.home(),"\\n"); print(.libPaths()); '+
        'for (p in c("Matrix","S4Vectors","jsonlite","digest","BiocVersion")) { '+
        'cat(p,": "); if (requireNamespace(p,quietly=TRUE)) cat(as.character(packageVersion(p)),"\\n") '+
        'else cat("UNAVAILABLE\\n") }; print(sessionInfo())'],renv)
    print('prepared independent provenance and availability receipts')

def acquire():
    if not (REPORT/'source_before.json').exists():
        raise SystemExit('prepare first')
    if (REPORT/'acquisition_attempts.json').exists():
        raise SystemExit('refuse repeated URL attempts')
    RAW.mkdir(exist_ok=False)
    entries = json.loads((REPORT/'acquisition_manifest.target.json').read_text())['artifacts']
    found = json.loads((REPORT/'real_file_availability.before.json').read_text())['candidates']
    attempts = []
    for name in NAMES:
        if any(Path(x['path']).name == name and x['matches_expected'] for x in found):
            attempts.append({'name':name,'action':'reuse_verified_existing','network_attempted':False})
            continue
        ent = next(x for x in entries if Path(x['path']).name == name)
        part = RAW/(name+'.download.part')
        headers = REPORT/'logs'/(name+'.headers.log')
        # Preserve inherited proxies and trust; no retries, alternates, mirrors or TLS bypass.
        argv = ['curl','--location','--fail','--silent','--show-error','--retry','0',
            '--connect-timeout','20','--max-time','60','--proto','=https',
            '--proto-redir','=https','--dump-header',str(headers),'--output',str(part),
            '--write-out','%{json}',ent['url']]
        rec, stdout, stderr = run(name+'_download',argv,timeout=65)
        try:
            curl = json.loads(stdout)
        except (ValueError,TypeError):
            curl = None
        actual = digest(part) if part.exists() else None
        matches = bool(actual and actual['bytes']==ent['bytes'] and actual['sha256']==ent['sha256'])
        if rec['exit_code']==0 and matches:
            part.rename(RAW/name)
        attempts.append({'name':name,'url':ent['url'],'attempt_count':1,
            'started_utc':rec['started_utc'],'ended_utc':rec['ended_utc'],
            'exit_code':rec['exit_code'],'stderr':stderr.decode(errors='replace'),
            'curl_metadata':curl,'partial_file':actual,'matches_expected':matches,
            'expected_bytes':ent['bytes'],'expected_sha256':ent['sha256'],
            'status':'ACQUIRED_VERIFIED' if rec['exit_code']==0 and matches else 'BLOCKED_ACQUISITION'})
        save(REPORT/'acquisition_attempts.json',attempts)
    print(json.dumps([{'name':x['name'],'status':x.get('status',x.get('action'))} for x in attempts]))

def seal():
    before = json.loads((REPORT/'source_before.json').read_text())
    after = source_state()
    save(REPORT/'source_after.json',after)
    save(REPORT/'source_preservation.json',{'same_HEAD':before['HEAD']==after['HEAD'],
        'same_audit_source_bytes':before['files']==after['files'],
        'clean_before':not before['status_porcelain'],'clean_after':not after['status_porcelain']})
    paths = [RAW/name for name in NAMES]
    save(REPORT/'real_file_availability.after.json', {'observed_utc':now(),
        'files':{str(path):{'exists':path.exists(),**(digest(path) if path.exists() else {})} for path in paths},
        'raw_sha_recomputed':any(path.exists() for path in paths),
        'unavailable_hashes_are_not_claimed':True})
    print('sealed source preservation and real-file availability')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','acquire','seal'])
    action=parser.parse_args().action
    {'prepare':prepare,'acquire':acquire,'seal':seal}[action]()
