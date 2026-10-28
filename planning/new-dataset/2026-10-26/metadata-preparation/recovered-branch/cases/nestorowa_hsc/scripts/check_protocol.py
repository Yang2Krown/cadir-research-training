#!/usr/bin/env python3
"""Validate the prepared design and expose unresolved formal-experiment gates."""
import argparse
import json
from pathlib import Path
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('protocol', type=Path)
parser.add_argument('--require-ready', action='store_true')
args = parser.parse_args()
p = json.loads(args.protocol.read_text())
assert len(p['seeds']) == 5 and len(set(p['seeds'])) == 5
assert p['CAdir']['dirclust_splitmerge']['k'] == 8
assert p['CAdir']['CA']['dims'] == p['baseline']['PCA']['ncomponents'] == 30
assert p['shared_input']['HVG']['n'] == 6000
assert not p['current_task_has_run_new_clustering_or_ARI_NMI']
assert p['dataset']['hub_fetch_ids'] == {'counts': 2710, 'coldata': 2711}
if p['blocking_conditions']:
    assert not p['formal_execution_permitted']
print(json.dumps({'status': 'DRAFT_STRUCTURE_VALID_BLOCKED' if p['blocking_conditions'] else 'REVIEW_REQUIRED',
                  'formal_execution_permitted': p['formal_execution_permitted'],
                  'blocking_conditions': p['blocking_conditions']}, indent=2))
if args.require_ready and not p['formal_execution_permitted']:
    raise SystemExit(2)
