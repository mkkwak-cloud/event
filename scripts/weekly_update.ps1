# 매주 월요일 07:00 작업 스케줄러가 실행: 수집 -> 대시보드 빌드 -> 게시·Notion 동기화
$ErrorActionPreference = 'Continue'
$proj = 'E:\12. 일반Project\event'
$root = Join-Path $proj 'scripts'
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'
$stamp = Get-Date -Format 'yyyyMMdd_HHmm'
$logDir = Join-Path $proj 'out\logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "weekly_$stamp.log"

"[$(Get-Date)] 수집 시작" | Out-File $log -Encoding utf8
python collect.py *>> $log
if ($LASTEXITCODE -ne 0) { "[$(Get-Date)] 수집 실패 - 중단" | Out-File $log -Append -Encoding utf8; exit 1 }

python build_dashboard.py *>> $log

$prompt = Get-Content (Join-Path $root 'notion_sync_prompt.md') -Raw -Encoding utf8
$prompt = $prompt.Replace('{{DASHBOARD_URL}}', (Get-Content (Join-Path $proj 'out\dashboard_url.txt') -Raw).Trim())
$tools = 'Read,ToolSearch,mcp__claude_ai_Notion__notion-query-data-sources,mcp__claude_ai_Notion__notion-create-pages,mcp__claude_ai_Notion__notion-update-page,mcp__claude_ai_Notion__notion-move-pages,mcp__claude_ai_Notion__notion-fetch,mcp__claude_ai_Notion__notion-update-data-source'
"[$(Get-Date)] 게시·Notion 동기화" | Out-File $log -Append -Encoding utf8
claude -p $prompt --allowedTools $tools *>> $log
"[$(Get-Date)] 완료" | Out-File $log -Append -Encoding utf8
