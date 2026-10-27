#!/usr/bin/env python3
"""Retain exact fixed-wrapper startup failures; these are not real-input reruns."""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
script = Path(__file__).with_name('independent_receipts.py')
spec = importlib.util.spec_from_file_location('independent_receipts', script)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

if (r.REPORT/'entry_startup_probes.json').exists():
    raise SystemExit('refuse to overwrite startup probes')
results = []
for mode in ['metadata-only','full']:
    output = r.REPORT/'entry-output'/mode
    assert not output.exists()
    args = [sys.executable, str(r.SOURCE/'cases/nestorowa_hsc/scripts/run_input_audit.py'),
        mode, '--metadata', str(r.RAW/'coldata.rds'),
        '--manifest', str(r.SOURCE/'planning/new-dataset/2026-10-26/metadata-preparation/acquisition_manifest.json'),
        '--output', str(output)]
    if mode == 'full':
        args += ['--counts',str(r.RAW/'counts.rds'),'--geo',str(r.RAW/'GSE81682_HTSeq_counts.txt.gz')]
    before = r.source_state()
    rec, stdout, stderr = r.run('wrapper_'+mode+'_startup',args)
    after = r.source_state()
    results.append({'mode':mode,'classification':'WRAPPER_PRECONDITION_FAILED_NOT_REAL_INPUT_RERUN',
        'execution':rec,'source_before':before,'source_after':after,
        'intended_raw_input_paths_exist':{str(p):p.exists() for p in
            ([r.RAW/'coldata.rds'] if mode=='metadata-only' else [r.RAW/n for n in r.NAMES])},
        'output_directory_exists':output.exists(),
        'target_execution_receipt_exists':output.with_suffix('.execution.json').exists(),
        'target_console_log_exists':output.with_suffix('.console.log').exists(),
        'raw_content_inspected':False,'audit_completed':False})
    r.save(r.REPORT/'entry_startup_probes.json',results)
    print(mode, 'startup exit',rec['exit_code'],'real-input rerun NOT COMPLETED')
