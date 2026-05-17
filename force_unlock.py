import os
import sys
sys.path.insert(0, r'C:\Users\lianjie\.openclaw\workspace\jingcai')
import protect

# Force unlock
lock_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\.locks\pipeline.lock'
if os.path.exists(lock_path):
    os.remove(lock_path)
    print('Lock file removed')
else:
    print('No lock file found')
