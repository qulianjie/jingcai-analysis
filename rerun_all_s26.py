# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, 'jingcai')
from step26_profit_ratio import run_profit_ratio_analysis

dates = ['2026-05-01','2026-05-02','2026-05-03','2026-05-04','2026-05-05','2026-05-06','2026-05-07','2026-05-08','2026-05-09']

for d in dates:
    print(f'\n=== 重新跑 {d} ===')
    run_profit_ratio_analysis(d)
