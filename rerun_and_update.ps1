# 重跑010-030并更新Notion
$ErrorActionPreference = 'Continue'
$PIPELINE = 'C:\Users\lianjie\.openclaw\workspace\jingcai\run_pipeline.py'
$SYNC = 'C:\Users\lianjie\.openclaw\workspace\jingcai\sync_notion.js'

# 清理锁
Remove-Item 'C:\Users\lianjie\.openclaw\workspace\jingcai\.locks\pipeline.lock' -Force -ErrorAction SilentlyContinue

# 重跑010-030
Write-Host "=== 重跑010-030 ===" -ForegroundColor Cyan
for ($i = 10; $i -le 30; $i++) {
    $num = $i.ToString("000")
    Write-Host "`n>>> 重跑 $num <<<" -ForegroundColor Yellow
    & python $PIPELINE $num 2>&1 | Select-Object -Last 3
}

# 更新Notion
Write-Host "`n=== 更新Notion ===" -ForegroundColor Cyan
node $SYNC update 2026-05-02 2>&1

Write-Host "`n=== 全部完成 ===" -ForegroundColor Green
