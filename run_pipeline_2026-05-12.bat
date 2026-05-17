@echo off
cd /d "C:\Users\lianjie\.openclaw\workspace"
python -u "jingcai\run_pipeline.py" 2026-05-12 > jingcai\pipeline_log.txt 2>&1
