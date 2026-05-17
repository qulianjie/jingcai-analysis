"""手动处理没加上的"""
for fp, name in [
    (r'C:\Users\lianjie\.openclaw\workspace\jingcai\final_conclusion_generator.py', 'final_concl'),
    (r'C:\Users\lianjie\.openclaw\workspace\jingcai\final_conclusion_generator_v2.py', 'final_concl_v2'),
    (r'C:\Users\lianjie\.openclaw\workspace\jingcai\step25_zhuangjia.py', 'step25'),
    (r'C:\Users\lianjie\.openclaw\workspace\jingcai\step26_profit_ratio.py', 'step26'),
    (r'C:\Users\lianjie\.openclaw\workspace\jingcai\final_report_generator.py', 'final_report'),
    (r'C:\Users\lianjie\.openclaw\workspace\jingcai\run_pipeline.py', 'pipeline'),
]:
    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查看前几行
    print(f'=== {fp.split(chr(92))[-1]} ===')
    for i, l in enumerate(lines[:8]):
        print(f'  L{i+1}: {l.rstrip()[:100]}')
    print()
