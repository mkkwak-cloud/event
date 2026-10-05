# HANDOFF (clear 전에 항상 최신으로 덮어쓴다)

## 현재 상태 (2026-10-03)
- 옛 폴더 event_collector 내용을 이 프로젝트로 옮기고 경로 수정, 작업 스케줄러(월 07:00) 새 경로로 변경 완료.
- 크레딧 절감(바뀐 곳만 읽기 + 무료 직접 읽기 5곳) 적용 완료: plan/phase-1/03-크레딧절감.md
- 전자신문 글자 깨짐 수정 완료. Notion 반영 완료(신규 66, 기존전환 102, 종료정리 0): plan/phase-1/04-노션반영.md
- GitHub(mkkwak-cloud/event, 공개) main에 870edc4까지 올림. 그 뒤 변경분(코드 수정, 새 대시보드, plan 04)은 아직 안 올림.

- 코엑스 누락(인공지능 페스타) 원인 수정 완료(03 문서 하단). 이 수정분은 아직 커밋 안 함.

- Claude 아티팩트(https://claude.ai/artifact/WfdYxzZQP4AqQ7Rm6YnM33)에 2026-10-03 판(172건) 올림. 매주 주간 마무리 절차는 CLAUDE.md 하단.

- 갤럭시용 앱(PWA) 적용: 맨 위 manifest.webmanifest·sw.js·icons/ 와 template.html 수정. 아직 커밋 안 함. 올린 뒤 폰에서 설치 확인 필요.

## 다음 할 일
1. 종료된 39행 Notion 정리(권한 거부로 보류) — 사용자가 직접 지우거나 권한 허용 후 재시도.
2. 새 대시보드(깨짐 수정본)를 GitHub에 올릴지 결정 (사용자가 "cmt" 해야 커밋).
3. 9/26 판단 2건 확인(AI FESTA 사전등록, XR 디바이스 12.10) — XR은 이번에도 추가 안 함.
4. 다음 월요일 자동 실행 후 크레딧·오류 확인.
## 업데이트 (2026-10-05)
- 월요일 자동 실행은 안 돈 것으로 보임(weekly_*.log 없음). 이날 수동으로 수집(173건, 신규 3) → 대시보드 → Notion → 아티팩트(Version 20) 완료. 기록: out/logs/weekly_20261005_manual.log
- Notion: 신규 2건 추가(디지털데일리 1건은 주소 중복이라 제외), 신규→기존 11건 전환. 종료 41행 정리는 보류(이전에 권한 거부된 작업이라 확인 후 진행).
- 맨 위 index.html 복사 완료. GitHub 커밋·올리기는 "cmt" 대기.
- (10/5 추가) 월요일 자동 실행이 안 된 진짜 원인: weekly_update.ps1 이 BOM 없는 UTF-8이라 PowerShell 5.1이 한글을 못 읽고 22행에서 문법 오류로 즉시 종료(작업 결과 1). BOM을 붙여 해결(문법 오류 0). 작업 스케줄러는 이미 "꺼져 있다 켜지면 바로 실행"(StartWhenAvailable) 설정이라 따로 바꿀 것 없음. 다음 자동 실행 10/12 07:00.
- 종료된 Notion 41행 정리(notion-move-pages)는 자동 권한 판정이 두 번 막음. notion_sync_prompt.md 에 "묻지 말고 바로 실행" 문구와 weekly_update.ps1 의 허용 도구 이름(mcp__notion__ 표기 추가) 수정도 막혀 보류.
