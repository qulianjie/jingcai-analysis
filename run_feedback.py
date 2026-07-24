import subprocess, sys, time
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')
target = datetime.fromordinal(datetime.now().toordinal() - 1).strftime('%Y-%m-%d')

print(f"Today: {today}, Target: {target}")
print("=" * 60)

# Step 1: Run feedback.js (with retry for transient network errors)
win_node = r'C:\Program Files\nodejs\node.exe'
win_js = r'C:\Users\lianjie\.openclaw\workspace\jingcai\feedback.js'

for attempt in range(1, 4):
    print(f"\n[Attempt {attempt}/3] Running feedback.js --date {today} ...")
    cmd = [win_node, '--max-old-space-size=512', win_js, '--date', today]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    if r.stdout:
        clean = '\n'.join(l for l in r.stdout.split('\n') if 'hermes-snap' not in l and 'hermes-cwd' not in l)
        if clean.strip():
            print(clean)
    
    if r.stderr:
        # Only show stderr if it's not just bash noise
        real_err = '\n'.join(l for l in r.stderr.split('\n') if 'hermes-snap' not in l and 'hermes-cwd' not in l and 'No such file' not in l)
        if real_err.strip():
            print("[STDERR]", real_err)
    
    print(f"Exit code: {r.returncode}")
    
    if r.returncode == 0:
        print("\n✅ Step 1 complete: feedback.js succeeded")
        break
    
    if attempt < 3:
        backoff = 15 * attempt
        print(f"⏳ Retrying in {backoff}s...")
        time.sleep(backoff)
    else:
        print("\n❌ feedback.js failed after 3 attempts")
        sys.exit(1)
