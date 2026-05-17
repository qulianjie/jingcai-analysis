// -*- coding: utf-8 -*-
"""测试 sync_notion.js 的数据提取"""
import os, subprocess, json, sys

# Find the actual report file
task_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10'
report_files = [f for f in os.listdir(task_dir) if f.endswith('.md') and '001' in f]
if not report_files:
    print('No report file found')
    sys.exit(1)

report_file = report_files[0]
report_path = os.path.join(task_dir, report_file)
print('Report: %s' % report_file)

# Find match dir
data_dir = os.path.join(task_dir, 'data')
match_dirs = [f for f in os.listdir(data_dir) if f.startswith('match1_')]
if not match_dirs:
    print('No match dir found')
    sys.exit(1)

match_dir = os.path.join(data_dir, match_dirs[0])
print('Match dir: %s' % match_dirs[0])

# Write a test script that uses the actual file paths
test_js = '''
const path = require('path');
const fs = require('fs');

const reportPath = process.argv[1];
const matchDir = process.argv[2];
const content = fs.readFileSync(reportPath, 'utf8');

// Test if report has summary table
function extractScoreFromTable(text, label) {
  const m = text.match(new RegExp('\\\\|\\\\s*' + label + '\\\\s*\\\\|\\\\s*([^|]+)\\\\|\\\\s*([^|]+)\\\\|'));
  if (m) {
    return m[1].trim() + ' | ' + m[2].trim();
  }
  return '';
}

console.log('=== Report table extraction ===');
console.log('欧赔趋势: ' + extractScoreFromTable(content, '欧赔趋势'));
console.log('IW同赔: ' + extractScoreFromTable(content, 'IW同赔'));
console.log('澳门亚盘: ' + extractScoreFromTable(content, '澳门亚盘'));
console.log('主队主场: ' + extractScoreFromTable(content, '主队主场'));
console.log('客队客场: ' + extractScoreFromTable(content, '客队客场'));
console.log('百家对比: ' + extractScoreFromTable(content, '百家对比'));

// Test data file extraction
function extractFromDataFiles() {
  const result = {};
  if (!matchDir || !fs.existsSync(matchDir)) return result;

  const g1Dir = path.join(matchDir, 'group01_europe');
  if (fs.existsSync(g1Dir)) {
    const s1 = path.join(g1Dir, 'step1_europe_base.txt');
    if (fs.existsSync(s1)) {
      const c1 = fs.readFileSync(s1, 'utf8');
      const scm = c1.match(/竞彩官方\\\\s*\\\\|\\\\s*([\\\\d.]+)\\\\s*\\\\|\\\\s*([\\\\d.]+)\\\\s*\\\\|\\\\s*([\\\\d.]+)\\\\s*\\\\|\\\\s*([\\\\d.]+)\\\\s*\\\\|\\\\s*([\\\\d.]+)\\\\s*\\\\|\\\\s*([\\\\d.]+)\\\\s*\\\\|\\\\s*([^|]+)/);
      if (scm) {
        result.oupei_base = '初盘' + scm[1] + '/' + scm[2] + '/' + scm[3] + '→即时' + scm[4] + '/' + scm[5] + '/' + scm[6];
      }
    }
    const s3 = path.join(g1Dir, 'step3_interwetten_same.txt');
    if (fs.existsSync(s3)) {
      const c3 = fs.readFileSync(s3, 'utf8');
      const iwCountMatch = c3.match(/Interwetten\\\\s*同赔\\\\s*共\\\\s*(\\\\d+)\\\\s*场/);
      if (iwCountMatch) {
        result.iw_same = iwCountMatch[1] + '场';
      }
    }
  }

  const g3Dir = path.join(matchDir, 'group03_asian');
  if (fs.existsSync(g3Dir)) {
    const s6 = path.join(g3Dir, 'step6_asian_base.txt');
    if (fs.existsSync(s6)) {
      const c6 = fs.readFileSync(s6, 'utf8');
      const macauMatch = c6.match(/澳门\\\\s*\\\\|\\\\s*([^|]+)\\\\s*\\\\|\\\\s*([^|]+)/);
      if (macauMatch) {
        result.macau_asian = '初盘' + macauMatch[1].trim() + ' 即时' + macauMatch[2].trim();
      }
    }
  }

  return result;
}

console.log('\\n=== Data file extraction ===');
const dataFiles = extractFromDataFiles();
for (const [k, v] of Object.entries(dataFiles)) {
  console.log(k + ': ' + v);
}
'''

# Write test script
test_path = os.path.join(os.path.dirname(__file__), 'test_extract.js')
with open(test_path, 'w', encoding='utf-8') as f:
    f.write(test_js)

# Run test
print('\nRunning extraction test...')
result = subprocess.run(
    ['node', test_path, report_path, match_dir],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)
print(result.stdout)
if result.stderr:
    print('STDERR:', result.stderr[:500])

# Cleanup
os.remove(test_path)
