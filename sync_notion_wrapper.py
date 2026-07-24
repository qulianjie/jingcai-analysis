# -*- coding: utf-8 -*-
"""Notion同步包装器 - 用 Windows Python 调 Windows Node 执行 sync_notion.js"""
from __future__ import print_function
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WIN_PYTHON = '/mnt/c/Python314/python.exe'
WIN_NODE = '/mnt/c/Program Files/nodejs/node.exe'


def _wsl_to_win(path):
    if path.startswith('/mnt/'):
        drive = path[5].upper()
        rest = path[7:].replace('/', '\\')
        return drive + ':\\' + rest
    return path


def _run_node(js_path, js_args):
    win_js = _wsl_to_win(js_path)
    win_node = _wsl_to_win(WIN_NODE)
    win_python = _wsl_to_win(WIN_PYTHON)

    tmp_py = os.path.join(SCRIPT_DIR, '___tmp_sync.py')
    win_tmp = _wsl_to_win(tmp_py)

    with open(tmp_py, 'w', encoding='utf-8') as f:
        f.write('import subprocess, sys\n')
        f.write('node = r"' + win_node + '"\n')
        f.write('js = r"' + win_js + '"\n')
        f.write('cmd = [node, js')
        for a in js_args:
            f.write(', r"' + a + '"')
        f.write(']\n')
        f.write('r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)\n')
        f.write('if r.stdout: print(r.stdout, end="")\n')
        f.write('if r.stderr: print(r.stderr, end="", file=sys.stderr)\n')
        f.write('sys.exit(r.returncode)\n')

    try:
        print('[INFO] 开始同步到Notion...', file=sys.stderr)
        result = subprocess.run([win_python, win_tmp],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=3600, universal_newlines=True)
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(line.strip())
        if result.returncode != 0:
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    if line.strip():
                        print(line.strip(), file=sys.stderr)
            sys.exit(result.returncode)
    finally:
        try:
            os.unlink(tmp_py)
        except:
            pass


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        args = ['add']
    _run_node(os.path.join(SCRIPT_DIR, 'sync_notion.js'), args)
