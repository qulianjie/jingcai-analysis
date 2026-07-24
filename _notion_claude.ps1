$TOKEN = Select-String -Path 'C:\Users\lianjie\.openclaw\workspace\jingcai\sync_notion.js' -Pattern 'ntn_[a-zA-Z0-9]+' | Select-Object -First 1 | ForEach-Object { $_.Matches.Value }

$body = @{
    parent = @{page_id = '35391ad7-17ba-80ae-9770-eb5d366fb56b'}
    properties = @{title = @(@{text = @{content = 'Claude Code十大必装Skill + 基础四件套'}})}
    markdown = @"
# Claude Code十大必装Skill + 基础四件套

来源：视频OCR识别整理

## 十大必装Skill

### 开发全流程类
1. Superpowers — 20+可组合Skill，擅长TDD
2. Planning with Files — 规划写入文件，上下文压缩不丢状态
3. Code Simplifier — 自动合并重复逻辑
4. Ralph Loop — 防提前收工

### 质量保障类
5. Code Review — 多Agent并行审查，置信度过滤
6. Webapp Testing — Playwright自动化测试

### UI/创意类
7. UI UX Pro Max — 67风格+161配色
8. PPTX — 直接生成PPTX

### 基建扩展类
9. MCP Builder — 搭建MCP Server
10. Skill Creator — 官方元技能

## 内置基础四件套
- Skill Creator（创建新技能）
- Web Access（网页数据读取）
- Playwright（浏览器自动化）
- Super Powers（代码开发全流程）

## 安装方式
.claude/skills/目录下放.md文件，Claude自动匹配加载
全局: ~/.claude/skills/ | 项目: .claude/skills/
"@
}

try {
    $r = Invoke-RestMethod -Uri 'https://api.notion.com/v1/pages' -Method Post `
        -Headers @{Authorization = "Bearer $TOKEN"; 'Content-Type' = 'application/json'; 'Notion-Version' = '2022-06-28'} `
        -Body ($body | ConvertTo-Json -Depth 3 -Compress)
    Write-Output "OK: $($r.id)"
} catch {
    Write-Output "FAIL: $($_.Exception.Message)"
}
