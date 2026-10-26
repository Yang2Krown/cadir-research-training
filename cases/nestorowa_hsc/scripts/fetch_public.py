#!/usr/bin/env python3
"""Fetch one public artifact through inherited proxy/TLS; log and preserve errors."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('url')
parser.add_argument('output', type=Path)
parser.add_argument('--max-bytes', type=int, default=128 * 1024 * 1024)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
if args.output.exists() or args.output.with_suffix(args.output.suffix + '.json').exists():
    raise SystemExit('Output or attempt record already exists; choose a new attempt path.')
record = {'url': args.url, 'started_utc': datetime.now(timezone.utc).isoformat()}
start = time.monotonic()
try:
    with urllib.request.urlopen(args.url, timeout=45) as response:
        data = response.read(args.max_bytes + 1)
        if len(data) > args.max_bytes:
            raise ValueError(f'Response exceeds predeclared byte limit {args.max_bytes}; no artifact accepted.')
        args.output.write_bytes(data)
        record.update(status=response.status, final_url=response.url, bytes=len(data),
                      sha256=hashlib.sha256(data).hexdigest(), headers=dict(response.headers))
except urllib.error.HTTPError as error:
    body = error.read()
    args.output.with_suffix(args.output.suffix + '.error').write_bytes(body)
    record.update(status=error.code, error=str(error), headers=dict(error.headers),
                  response_body=body.decode(errors='replace')[:2000])
except Exception as error:
    record['error'] = str(error)
record['elapsed_seconds'] = time.monotonic() - start
args.output.with_suffix(args.output.suffix + '.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
raise SystemExit(0 if record.get('status') == 200 else 1)
