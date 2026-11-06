"""Allowlisted, reproducible source release with a candidate-file secret/artifact check.
Does not commit, push, deploy, read ignored .env files, or inspect Git history.
"""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = {'apps','packages','infrastructure','docs','scripts','.github'}
ROOT_FILES = {'README.md','CONTRIBUTING.md','SECURITY.md','LICENSE','THIRD_PARTY.md','Makefile','.env.example','.gitignore','.dockerignore','docker-compose.yml','docker-compose.test.yml'}
SKIP = {'node_modules','.next','.venv','venv','__pycache__','.pytest_cache','.ruff_cache','uploads','test-results','playwright-report','artifacts','.git','coverage','validation-output'}
BANNED = {'.db','.sqlite','.sqlite3','.pyc','.zip','.log','.pem','.key','.tsbuildinfo','.sql','.dump','.tar','.gz'}
SECRETS = [re.compile(p) for p in [r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{40,}',r'AKIA[0-9A-Z]{16}',r'sk-(?:proj-)?[A-Za-z0-9_-]{30,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']]

def candidate_files():
    try:
        names = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT,stderr=subprocess.DEVNULL).decode().split('\0')
        paths = [ROOT/name for name in names if name]
        if not paths:raise ValueError('Empty index')
    except (subprocess.CalledProcessError,FileNotFoundError,ValueError):
        paths = list(ROOT.rglob('*'))
    candidates=[]
    for path in paths:
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(part in SKIP for part in rel.parts):continue
        if rel.parts[0] not in TOP and str(rel) not in ROOT_FILES:continue
        if path.is_symlink():raise ValueError('Symlink not allowed: '+str(rel))
        if path.suffix in BANNED or '.db-' in path.name or (path.name.startswith('.env') and path.name!='.env.example'):
            raise ValueError('Release artifact or environment file: '+str(rel))
        # Curated screenshots are intentional documentation assets, not raw browser outputs.
        if path.suffix=='.png' and rel.parts[:2]!=('docs','images'):
            raise ValueError('Unexpected image artifact: '+str(rel))
        if path.suffix not in {'.png','.jpg','.jpeg'}:
            content=path.read_text(encoding='utf-8')
            if any(pattern.search(content) for pattern in SECRETS):
                raise ValueError('Potential secret in '+str(rel)+' (review privately)')
        candidates.append(path)
    return sorted(candidates)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--output',type=Path,default=ROOT.parent/'knowledgeforge-ai-git-ready.zip');args=parser.parse_args()
    files=candidate_files()
    if not files:raise ValueError('No source files')
    if args.check:
        print(f'PASS: {len(files)} candidate source files; no banned artifacts or known token/private-key patterns')
        return
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            entry=zipfile.ZipInfo('knowledgeforge-ai/'+str(path.relative_to(ROOT)),date_time=(2026,1,1,0,0,0))
            entry.external_attr=(0o100755 if path.name.endswith('.sh') else 0o100644)<<16
            entry.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(entry,path.read_bytes())
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    digest=hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix('.sha256').write_text(digest+'  '+args.output.name+'\n')
    print(f'Created {args.output.name}: {len(files)} files, {args.output.stat().st_size:,} bytes; SHA256 {digest}')

if __name__=='__main__':main()
