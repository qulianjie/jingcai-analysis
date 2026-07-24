import subprocess; r=subprocess.run(["node","C:/Users/lianjie/.openclaw/workspace/jingcai/sync_notion.js","add","2026-05-29","001,002,003,004,005,006,007,008,009"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120); print(r.stdout.decode("utf-8")[:3000])
print("EXIT:",r.returncode)
err = r.stderr.decode("utf-8",errors="replace")[:500];
if err: print("ERR:",err)