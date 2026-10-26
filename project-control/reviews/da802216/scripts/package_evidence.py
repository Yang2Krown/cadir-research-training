#!/usr/bin/env python3
"""Package only this review, excluding the package and its own hash index recursion."""
import hashlib,pathlib,shutil,zipfile,json
B=pathlib.Path(__file__).resolve().parents[1];ROOT=B.parents[2];D=ROOT/'delivery';D.mkdir(exist_ok=True)
files=sorted(p for p in B.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='evidence_sha256.tsv')
with (B/'evidence_sha256.tsv').open('w') as f:
 f.write('path\tbytes\tsha256\n')
 for p in files:f.write(f'{p.relative_to(B)}\t{p.stat().st_size}\t{hashlib.sha256(p.read_bytes()).hexdigest()}\n')
files.append(B/'evidence_sha256.tsv');z=D/'hsc-input-independent-review-evidence-20261026.zip'
with zipfile.ZipFile(z,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as out:
 for p in files:out.write(p,str(pathlib.Path(B.name)/p.relative_to(B)))
h=hashlib.sha256(z.read_bytes()).hexdigest();(D/(z.name+'.sha256')).write_text(h+'  '+z.name+'\n')
local=pathlib.Path('/workspace')/z.name;shutil.copyfile(z,local)
print(json.dumps({'ZIP':str(z),'copy':str(local),'bytes':z.stat().st_size,'sha256':h,'files_in_ZIP':len(files)}))
