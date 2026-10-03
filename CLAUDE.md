이 폴더는 행사 정보 수집·대시보드 프로젝트다.
처음 시작할 때는 내 말을 plan/phase-1/01-상황.md 에 받아쓰고 위 첫 줄의 (주제)를 채운 뒤, 이 폴더에서 git init 하고 "시작"으로 첫 커밋한다.
폴더 역할 — plan/: 계획·결정, phase 별로 나누고 파일은 01-부터 번호. data/: 받은 파일, 고치지 않는다. out/: 만든 결과물. scripts/: 네가 짠 도구.
흐름이 크게 바뀌면 plan/phase-2/ 를 새로 만든다. 새 일은 번호를 늘려 새 파일, 옛 파일은 지우지 않는다.
다른 폴더가 필요하면 영문 이름으로 만들고 이 파일에 역할을 한 줄 적는다.
HANDOFF.md 에 현재 상태와 다음 할 일을 적어 두고, clear 하기 전에 항상 최신으로 덮어쓴다.
내 수준에 맞춰 전문용어 없이 말해라. 애매하면 먼저 물어라.
scripts/ 안 파일: collect.py(행사 수집), build_dashboard.py(대시보드 만들기), eventus_search.py(이벤터스 검색), weekly_update.ps1(매주 월요일 07:00 자동 실행 묶음), notion_sync_prompt.md(Notion 반영 지시문), probe.py(사이트 점검용).
out/dashboard/: 대시보드 화면. out/logs/: 실행 기록. out/probe/: 점검 결과.
scripts/direct_parsers.py(무료 직접 읽기), probe_free.py(무료 읽기 시험), collect.py.bak(고치기 전 백업). data/page_hash.json(바뀐 곳 감지용 기록), data/_backup_20261003/(백업).
주간 절차 — 월요일 07:00 자동 실행(수집·대시보드·Notion)이 끝나면, 대화에서 "주간 마무리"라고 하면 다음을 한다: (1) out/dashboard/index.html 을 기존 Claude 아티팩트(주소는 out/dashboard_url.txt)에 같은 주소로 덮어 올린다 (2) 수집 오류·건수 급감이 없는지 out/logs 최신 기록을 확인한다 (3) 종료된 Notion 행 정리가 남았는지 알린다 (4) out/dashboard/index.html 을 이 폴더 맨 위의 index.html 로 복사해 둔다(GitHub 페이지용, 올리는 건 "cmt" 때). 자동 실행은 아티팩트를 직접 못 올리므로 이 단계는 대화에서만 가능하다. GitHub 커밋·올리기는 "cmt"라고 할 때만.
앱(PWA) 파일: 맨 위의 manifest.webmanifest(앱 이름·아이콘 설정), sw.js(오프라인용), icons/(앱 아이콘, scripts/make_icons.py 로 만듦). 대시보드 틀은 out/dashboard/template.html 이고, 앱 설치 버튼·서비스워커 등록이 거기에 들어 있다. GitHub 페이지에서만 앱 설치가 동작한다.
