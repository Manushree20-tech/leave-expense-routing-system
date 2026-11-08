import argparse,hashlib,subprocess,sys,tempfile
from pathlib import Path
def hashes(folder):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(folder).iterdir() if p.is_file()}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,default=20261022); ap.add_argument('--employees',type=int,default=400); ap.add_argument('--leave-requests',type=int,default=800); ap.add_argument('--expense-claims',type=int,default=1000); a=ap.parse_args()
    root=Path(__file__).resolve().parents[1]; script=root/'generator'/'generate_data.py'
    with tempfile.TemporaryDirectory() as t:
        a1=Path(t)/'run1'; a2=Path(t)/'run2'
        common=[sys.executable,str(script),'--seed',str(a.seed),'--employees',str(a.employees),'--leave-requests',str(a.leave_requests),'--expense-claims',str(a.expense_claims)]
        subprocess.run(common+['--out',str(a1)],check=True,cwd=root,capture_output=True)
        subprocess.run(common+['--out',str(a2)],check=True,cwd=root,capture_output=True)
        h1=hashes(a1); h2=hashes(a2); same=h1==h2
        print({'same_seed':a.seed,'file_count':len(h1),'all_checksums_match':same,'mismatched_files':sorted(set(h1)^set(h2) | {k for k in h1.keys()&h2.keys() if h1[k]!=h2[k]})})
        return 0 if same else 1
if __name__=='__main__': raise SystemExit(main())
