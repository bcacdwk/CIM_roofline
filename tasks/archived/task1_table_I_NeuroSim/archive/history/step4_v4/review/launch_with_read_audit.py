#!/usr/bin/env python3
"""Run the isolated V4 entry while auditing Python file reads in this process and inherited workers."""
import os, pathlib, subprocess, sys, json, textwrap
here=pathlib.Path(__file__).resolve().parent
hook=here/'audit_hook';hook.mkdir(exist_ok=True)
(hook/'sitecustomize.py').write_text('''import os,sys,json\nlog=os.environ.get("V4_REVIEW_OPEN_LOG")\nbusy=False\ndef audit(event,args):\n global busy\n if busy or not log or event not in ("open","subprocess.Popen"):return\n try:\n  busy=True\n  with open(log+"."+str(os.getpid()),"a") as out:out.write(json.dumps({"event":event,"args":[str(a)[:1000] for a in args[:3]]})+"\\n")\n finally:busy=False\nsys.addaudithook(audit)\n''')
env=dict(os.environ,PYTHONPATH=str(hook),V4_REVIEW_OPEN_LOG=str(here/'open_audit'),PYTHONDONTWRITEBYTECODE='1')
args=[sys.executable,'-B',*sys.argv[1:]]
result=subprocess.run(args,env=env)
raise SystemExit(result.returncode)
