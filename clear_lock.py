import os, json
from datetime import datetime

LOCK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.locks')
name = 'pipeline'
lock_file = os.path.join(LOCK_DIR, '%s.lock' % name)

if os.path.exists(lock_file):
    os.remove(lock_file)
    print('Removed %s' % lock_file)
else:
    print('Lock file does not exist')
