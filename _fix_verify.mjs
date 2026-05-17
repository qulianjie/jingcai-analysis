const fs = require('fs');
const path = require('path');
const source = path.join('jingcai', 'run_pipeline.py');
let content = fs.readFileSync(source, 'utf8');

// Edit 1: Replace the check call + persist_verify_result function
const old1 = `    # ============ 数据质量核查 ============
    verify_ok = verify_match_data(match_dir, home, away)
    if not verify_ok:
        log('WARN', '数据质量核查未通过: {} vs {}'.format(home, away))
    # 无论通过与否，都将核查结果持久化到文件
    persist_verify_result(match_dir, home, away, verify_ok)
    
    return True

def persist_verify_result(match_dir, home, away, passed):
    """将核查结果持久化到 verify_result.json"""
    import os, json
    result_path = os.path.join(match_dir, 'verify_result.json')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result = {
        'passed': passed,
        'checked_at': now,
        'match': '{} vs {}'.format(home, away),
    }
    if not passed:
        # 重新读issues（如果不通过，print里已经输出了，这里重新收集）
        import io as _io
        old_stdout = sys.stdout
        sys.stdout = _io.StringIO()
        passed2 = verify_match_data(match_dir, home, away)
        captured = sys.stdout.getvalue()
        sys.stdout = old_stdout
        result['issues'] = [l.strip() for l in captured.split('\n') if '⚠️' in l]
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log('VERIFY', '核查结果已持久化: {}'.format(result_path))`;

const new1 = `    # ============ 数据质量核查（第一次：只记录，不修正）============
    passed, issues = verify_match_data(match_dir, home, away)
    _save_verify_result(match_dir, home, away, passed, issues)
    if issues:
        log('CHECK', '🔍 {} vs {} 发现{}项（已记录，不修正）'.format(home, away, len(issues)))
    else:
        log('CHECK', '✅ {} vs {} 数据完整'.format(home, away))
    
    return True

def _save_verify_result(match_dir, home, away, passed, issues):
    """持久化核查结果到 verify_result.json"""
    import os, json
    result_path = os.path.join(match_dir, 'verify_result.json')
    result = {
        'passed': passed,
        'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'match': '{} vs {}'.format(home, away),
        'issues': issues,
    }
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)`;

if (content.includes(old1)) {
    content = content.replace(old1, new1);
    console.log('Edit 1 done');
} else {
    console.log('Edit 1 NOT FOUND');
    // debug: find the unique part
    const idx = content.indexOf('============ 数据质量核查 ============');
    if (idx >= 0) console.log('Found at', idx, 'End:', JSON.stringify(content.substring(idx, idx+200)));
}

// Edit 2: docstring
content = content.replace(
    '    """核查单场比赛的数据质量，返回是否通过"""',
    '    """核查单场比赛的数据质量，返回 (passed, issues)"""'
);
console.log('Edit 2 done');

// Edit 3: return values
const old3 = `    if issues:
        print('[VERIFY] 发现{}个问题:'.format(len(issues)))
        for iss in issues:
            print('[VERIFY]   ⚠️ {}'.format(iss))
        return False
    else:
        print('[VERIFY] ✅ 数据质量核查通过')
        return True`;

const new3 = `    return (len(issues) == 0, issues)`;

if (content.includes(old3)) {
    content = content.replace(old3, new3);
    console.log('Edit 3 done');
} else {
    console.log('Edit 3 NOT FOUND');
}

// Also update _summarize to read from saved files instead of re-calling
// The _summarize function should use the saved verify_result.json, not re-call verify_match_data
const old4 = `def _summarize_verify_results(date_str):
    """汇总当天所有比赛的核查结果，写入 data/verify_summary.json"""
    import os, json
    data_dir = os.path.join(TASKS_DIR, date_str, 'data')
    if not os.path.exists(data_dir):
        log('VERIFY_SUMMARY', 'data目录不存在: {}'.format(data_dir))
        return
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for d in sorted(os.listdir(data_dir)):
        if not d.startswith('match'):
            continue
        vp = os.path.join(data_dir, d, 'verify_result.json')
        if not os.path.exists(vp):
            results.append({'match_dir': d, 'passed': 'unknown', 'reason': '无核查记录'})
            continue
        with open(vp, 'r', encoding='utf-8') as f:
            r = json.load(f)
        if r.get('passed'):
            passed_count += 1
        else:
            failed_count += 1
        results.append({
            'match_dir': d,
            'match': r.get('match', ''),
            'passed': r.get('passed'),
            'checked_at': r.get('checked_at', ''),
            'issues': r.get('issues', []),
        })
    
    summary = {
        'date': date_str,
        'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(results),
        'passed': passed_count,
        'failed': failed_count,
        'details': results,
    }
    
    summary_path = os.path.join(data_dir, 'verify_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    log('VERIFY_SUMMARY', '✅ {}通过, ❌ {}未通过, 共{}场'.format(passed_count, failed_count, len(results)))
    log('VERIFY_SUMMARY', '汇总写入: {}'.format(summary_path))
    
    if failed_count > 0:
        log('VERIFY_SUMMARY', '--- 未通过比赛 ---')
        for r in results:
            if r['passed'] in (False, 'unknown'):
                log('VERIFY_SUMMARY', '  ❌ {}: {}'.format(r.get('match', r['match_dir']), r.get('issues', ['无记录'])))`;

if (content.includes(old4)) {
    content = content.replace(old4, old4); // no change needed, it already reads from files
    console.log('_summarize unchanged (already reads from files)');
}

fs.writeFileSync(source, content, 'utf8');
console.log('\nFile saved. Checking...');

// Verify no corruption
const check = fs.readFileSync(source, 'utf8');
const vf = check.indexOf('def verify_match_data');
const ps = check.indexOf('def _summarize_verify_results');
console.log('verify_match_data at line', check.substring(0, vf).split('\n').length);
console.log('_summarize at line', check.substring(0, ps).split('\n').length);
console.log('return (len(issues) == 0, issues) found:', check.includes('return (len(issues) == 0, issues)'));
console.log('_save_verify_result found:', check.includes('def _save_verify_result'));
console.log('old persist_verify_result still present:', check.includes('def persist_verify_result'));
