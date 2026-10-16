# 매주 월요일 09:00 작업 스케줄러가 실행 (못 돌면 PC 켜진 뒤·로그인 때 자동 보충): 수집 -> 대시보드 빌드 -> 게시·Notion 동기화
$ErrorActionPreference = 'Continue'
$proj = 'E:\12. 일반Project\event'
$root = Join-Path $proj 'scripts'
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'

# 이번 주 월요일 09:00 이후 성공 기록이 이미 있으면 건너뜀 (PC 켤 때마다 불려도 주 1회만 실행)
$marker = Join-Path $proj 'out\last_success.txt'
$now = Get-Date
$due = $now.Date.AddDays(-(([int]$now.DayOfWeek + 6) % 7)).AddHours(9)
if ($due -gt $now) { $due = $due.AddDays(-7) }
if ((Test-Path $marker) -and ((Get-Item $marker).LastWriteTime -ge $due)) { exit 0 }

$stamp = Get-Date -Format 'yyyyMMdd_HHmm'
$logDir = Join-Path $proj 'out\logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "weekly_$stamp.log"

"[$(Get-Date)] 수집 시작" | Out-File $log -Encoding utf8
py collect.py *>> $log
if ($LASTEXITCODE -ne 0) { "[$(Get-Date)] 수집 실패 - 중단" | Out-File $log -Append -Encoding utf8; exit 1 }

py build_dashboard.py *>> $log
if ($LASTEXITCODE -ne 0) { "[$(Get-Date)] 대시보드 빌드 실패 - 중단" | Out-File $log -Append -Encoding utf8; exit 1 }

$prompt = Get-Content (Join-Path $root 'notion_sync_prompt.md') -Raw -Encoding utf8
$prompt = $prompt.Replace('{{DASHBOARD_URL}}', (Get-Content (Join-Path $proj 'out\dashboard_url.txt') -Raw).Trim())
$tools = 'Read,ToolSearch,mcp__claude_ai_Notion__notion-query-data-sources,mcp__claude_ai_Notion__notion-create-pages,mcp__claude_ai_Notion__notion-update-page,mcp__claude_ai_Notion__notion-move-pages,mcp__claude_ai_Notion__notion-fetch,mcp__claude_ai_Notion__notion-update-data-source,mcp__notion__notion-query-data-sources,mcp__notion__notion-create-pages,mcp__notion__notion-update-page,mcp__notion__notion-move-pages,mcp__notion__notion-fetch,mcp__notion__notion-update-data-source'
"[$(Get-Date)] 게시·Notion 동기화" | Out-File $log -Append -Encoding utf8
claude -p $prompt --allowedTools $tools *>> $log

# 폰(GitHub 페이지)용 갱신: index.html 한 파일만 복사·커밋·올림
"[$(Get-Date)] 폰용 게시" | Out-File $log -Append -Encoding utf8
Copy-Item (Join-Path $proj 'out\dashboard\index.html') (Join-Path $proj 'index.html') -Force
Set-Location $proj
git add index.html *>> $log
git commit -m "주간 자동 갱신 $(Get-Date -Format 'yyyy-MM-dd')" -- index.html *>> $log
git push origin main *>> $log
if ($LASTEXITCODE -ne 0) { "[$(Get-Date)] 폰용 게시 실패 - 다음 실행 때 재시도" | Out-File $log -Append -Encoding utf8; exit 1 }

"[$(Get-Date)] 완료" | Out-File $log -Append -Encoding utf8
Set-Content $marker (Get-Date -Format 'yyyy-MM-dd HH:mm') -Encoding utf8
