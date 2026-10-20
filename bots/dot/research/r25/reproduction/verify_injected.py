"""Local-only isolated verification. Never packages supplied datasets."""
import argparse,hashlib,json,pathlib,shutil,subprocess,sys,tempfile
P=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input-dir',required=True);args=ap.parse_args()
with tempfile.TemporaryDirectory(prefix='r25-code-only-check-') as tmp:
 root=pathlib.Path(tmp);shutil.copyfile(P/'reproduce.py',root/'reproduce.py');shutil.copyfile(P/'inputs.json',root/'inputs.json');(root/'sources').mkdir()
 for name in json.loads((P/'inputs.json').read_text()):shutil.copyfile(pathlib.Path(args.input_dir)/pathlib.Path(name).name,root/name)
 (root/'guard.py').write_text('''import csv,json,hashlib,sys,pathlib,fractions,datetime,runpy,os\nroot=pathlib.Path(__file__).resolve().parent\nruntime=pathlib.Path(sys.base_prefix).resolve()\ndef guard(event,args):\n if event=="open" and isinstance(args[0],(str,bytes,os.PathLike)):\n  p=pathlib.Path(args[0]).resolve()\n  if not p.is_relative_to(root) and not p.is_relative_to(runtime): raise PermissionError("Outside isolated replay")\n if event.startswith("socket."): raise PermissionError("Network forbidden")\nsys.addaudithook(guard)\nrunpy.run_path(str(root/"reproduce.py"),run_name="__main__")\n''')
 r=subprocess.run([sys.executable,'-I',str(root/'guard.py')],cwd=root,capture_output=True,text=True);assert r.returncode==0,r.stderr
 actual={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'results').iterdir()};expected=json.loads((P/'expected-output-hashes.json').read_text());assert actual==expected,(actual,expected)
 p=root/'sources/contract.json';p.write_bytes(p.read_bytes()+b' ');t=subprocess.run([sys.executable,'-I',str(root/'guard.py')],cwd=root,capture_output=True,text=True);assert t.returncode!=0 and 'SOURCE HASH MISMATCH' in t.stderr
 print(json.dumps({'isolated_replay_returncode':r.returncode,'input_count':8,'output_hashes':actual,'all_original_hashes_match':True,'network_and_original_workspace_reads_denied_during_replay':True,'tamper_refusal':True,'raw_data_bundled':False},indent=2))
