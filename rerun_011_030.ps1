# 重跑011-030竞彩流水线
$ErrorActionPreference = 'Continue'
$PIPELINE = 'C:\Users\lianjie\.openclaw\workspace\jingcai\run_pipeline.py'

# 清理锁
Remove-Item 'C:\Users\lianjie\.openclaw\workspace\jingcai\.locks\pipeline.lock' -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$SUCCESS = 0
$FAIL = 0

for ($i = 11; $i -le 30; $i++) {
    $num = $i.ToString("000")
    Write-Host "`n>>> 重跑 $num <<<" -ForegroundColor Cyan
    
    $output = & python $PIPELINE $num 2>&1 | ForEach-Object { $_ }
    $lastLines = $output | Select-Object -Last 3
    
    if ($lastLines -match "全部完成") {
        Write-Host "  ✅ 成功" -ForegroundColor Green
        $SUCCESS++
    } else {
        Write-Host "  ❌ 失败" -ForegroundColor Red
        $lastLines | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
        $FAIL++
    }
    
    Start-Sleep -Seconds 2
}

Write-Host "`n>>> 完成: 成功 $SUCCESS, 失败 $FAIL <<<" -ForegroundColor Green
