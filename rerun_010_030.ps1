# 重跑010-030竞彩流水线
$ErrorActionPreference = 'Continue'
Remove-Item 'C:\Users\lianjie\.openclaw\workspace\jingcai\.locks\pipeline.lock' -Force -ErrorAction SilentlyContinue

$PIPELINE = 'C:\Users\lianjie\.openclaw\workspace\jingcai\run_pipeline.py'

for ($i = 10; $i -le 30; $i++) {
    $num = $i.ToString("000")
    Write-Host "`n>>> 重跑 $num <<<" -ForegroundColor Cyan
    & python $PIPELINE $num 2>&1 | ForEach-Object { $_ }
}

Write-Host "`n>>> 全部完成 <<<" -ForegroundColor Green
