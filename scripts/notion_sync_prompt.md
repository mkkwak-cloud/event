주간 행사 수집 결과를 대시보드와 Notion에 반영하는 작업입니다. 작업 폴더는 `E:\12. 일반Project\event`입니다.

1. **Notion 동기화**: `data/events.json`의 `events`를 Notion 데이터 소스 `collection://872e669f-3489-408f-b593-f2284e656198`와 맞춥니다.
   - 기존 행 조회는 반드시 view 모드를 쓰세요 (SQL·rows 모드는 워크스페이스 한도에 걸립니다):
     `notion-query-data-sources {"data":{"mode":"view","view_url":"view://3e4f4e59-0022-8165-84ac-000c64f535ab","page_size":100}}` — `has_more`가 true면 `start_cursor`로 이어서 조회.
   - events.json의 행사 중 Notion에 없는 것(원문URL이 같거나, 행사명이 거의 같고 시작일이 같으면 같은 행사)만 `notion-create-pages`로 한 번에 추가합니다. 속성 매핑:
     행사명=title, 분야태그=tags, 유형=notion_kind, 시작일=start, 종료일=end, 등록마감일=deadline(없으면 생략), 장소=place, 온라인여부=online(빈 값이면 오프라인), 주최=host, 참가비=fee, 원문URL=url, 수집일=오늘, 최초발견일=first_seen, 상태=신규.
   - 상태가 '신규'인데 최초발견일이 7일 이상 지난 기존 행은 상태를 '기존'으로 바꿉니다.
   - 종료일이 오늘보다 이전인 행은 `notion-move-pages`로 `{"type":"workspace"}`에 옮겨 DB에서 빼냅니다. 매주 하는 정해진 정리 작업이니 묻지 말고 조회한 모든 페이지(나눠 조회한 것 포함)에서 바로 실행하세요. 종료일이 비어 있으면 시작일로 판단하고, 100개가 넘으면 나눠서 옮기세요.
   - 같은 행사를 두 번 만들지 마세요.
   - 분야태그에 DB 선택지에 없는 값(예: `AI일반`)이 있어 생성이 실패하면, `notion-update-data-source`로 분야태그 선택지에 그 값을 추가한 뒤 다시 시도하세요.
   - 한 번에 너무 많으면 50건씩 나눠 생성하세요.

2. 마지막 줄에 `신규 N건 · 기존전환 N건 · 종료정리 N건`을 한 줄로 남기세요.

(대시보드 `out/dashboard/index.html`은 앞 단계에서 이미 로컬로 갱신됩니다. 헤드리스 실행에는 Artifact 도구가 없어 공유 링크 {{DASHBOARD_URL}} 재게시는 대화형 세션에서 합니다.)
