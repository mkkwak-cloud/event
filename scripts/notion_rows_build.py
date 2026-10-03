"""Notion 기존 행 조회 결과(2쪽)를 합쳐 data/notion_sync/notion_rows.json 으로 저장하는 일회성 도구."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
F1 = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "notion_sync")
os.makedirs(OUT, exist_ok=True)


def mk(r):
    return {"id": r["url"].rsplit("/", 1)[1].replace("-", ""), "url": r.get("원문URL", ""),
            "title": r.get("행사명", ""), "start": r.get("date:시작일:start"), "end": r.get("date:종료일:start"),
            "status": r.get("상태"), "fs": r.get("date:최초발견일:start")}


rows = [mk(r) for r in json.load(open(F1, encoding="utf-8"))["results"]]

# 2쪽 (화면에서 옮겨 적음): id, 원문URL, 행사명(앞부분), 시작일, 상태, 최초발견일
P2 = [
    ("3e4f4e59002281919ccac709a7d0438b", "https://amxpo.org/main/?mc_code=101010", "AMXPO 2026", "2026-10-21", "신규", "2026-09-23"),
    ("3e4f4e59002281158241d6c04744db9f", "https://edu.katech.re.kr/core/?cid=24&role=classview&lectureuid=294", "미래차·AI 기능안전 표준 4차", "2026-10-21", "기존", "2026-09-23"),
    ("3e4f4e590022819d8093c3b5adc75063", "https://industrialaiexpo.or.kr/Contents.asp?LoadPage=Programall", "2026 산업AI EXPO", "2026-10-21", "기존", "2026-09-23"),
    ("3e4f4e590022813ca83ccf1b7722a550", "https://fixkorea.or.kr/main.asp", "FIX 2026", "2026-10-21", "기존", "2026-09-23"),
    ("3e7f4e59002281f3b815fded5cbbb732", "https://onoffmix.com/event/348293", "[전북] AI를 활용한 비즈니스 모델 분석 향상 과정", "2026-10-22", "신규", "2026-09-26"),
    ("3e4f4e5900228147a662d510b04d38d8", "https://event-us.kr/azwellai/event/135306", "AI Acceleration Day", "2026-10-22", "신규", "2026-09-24"),
    ("3e4f4e59002281858235c82919fafeee", "https://event-us.kr/ITwkuIC3lSfi/event/134138", "트렌드쇼 2027 : AI 아젠다", "2026-10-22", "신규", "2026-09-24"),
    ("3e4f4e59002281f1bb2de1613fd3b1dc", "https://event-us.kr/qF6WC3gQqh2Z/event/130140", "2027 테크 퀘스트 TECH QUEST", "2026-10-22", "신규", "2026-09-24"),
    ("3e4f4e59002281f79431f6a6829d2e64", "https://event-us.kr/mcloudbridge/event/135564", "엠클라우드브리지 Ai 365", "2026-10-22", "신규", "2026-09-24"),
    ("3e4f4e590022817c92fbda87b1feecff", "https://aiax.etnews.com/", "AX & 하이퍼오토메이션 코리아 2026-Fall", "2026-10-23", "신규", "2026-09-24"),
    ("3e4f4e5900228181bd28e4029bb55312", "https://event-us.kr/hrdkitanet/event/135700", "10/23 AI 자동화 마스터 n8n", "2026-10-23", "신규", "2026-09-24"),
    ("3e4f4e59002281b4b802e2fac805ad0d", "https://event-us.kr/insadream/event/128492", "함수 몰라도 OK AI와 대화하며 엑셀", "2026-10-23", "신규", "2026-09-24"),
    ("3e4f4e59002281fb91b1efe8209fbe85", "https://event-us.kr/kbedu/event/135931", "2026 교육심포지엄 AI 불안주의보", "2026-10-23", "신규", "2026-09-24"),
    ("3e4f4e59002281228425d7d1318fd7c3", "https://event-us.kr/icskorea/event/134617", "10BASE-T1S Training 5기", "2026-10-23", "신규", "2026-09-24"),
    ("3e4f4e59002281bb92b6dc54ef0d17b9", "https://event-us.kr/daton/event/132785", "2026 청년기업 AX 리더십 파트너스데이", "2026-10-23", "신규", "2026-09-24"),
    ("3e4f4e590022814d9616ff45561fd91f", "https://www.sw.or.kr/upload/edu/1339522d-b53f-4b85-b4ac-89e627aaed28.png", "[컨소시엄] 품질관리를 위한 클린코드", "2026-10-24", "신규", "2026-09-24"),
    ("3e4f4e59002281aba8bcf3fa24fd3eee", "https://event-us.kr/eduwilledu/event/135598", "(산대특) 직장인 생존 AI 노코드", "2026-10-24", "신규", "2026-09-24"),
    ("3e4f4e5900228173b6beec6e7ece7138", "https://onoffmix.com/event/350253", "(이해) 빅데이터와 AI 이해 및 활용(3기)", "2026-10-26", "신규", "2026-09-24"),
    ("3e4f4e59002281e4be96f061c116f937", "https://event-us.kr/insadream/event/130885", "AI를 활용한 교육과정개발 실무과정", "2026-10-27", "신규", "2026-09-24"),
    ("3e4f4e590022812286caf33eccc3ad48", "https://event-us.kr/functionalsafety/event/135286", "FSG Korea Functional Safety Conference 2026", "2026-10-27", "신규", "2026-09-24"),
    ("3e4f4e59002281b8bb4df75b946a35ab", "https://event-us.kr/seminarhub/event/134885", "AI 반도체 패키징 광인터커넥트 CPO", "2026-10-27", "신규", "2026-09-24"),
    ("3e4f4e59002281bab34ad3661c6f1c9e", "https://event-us.kr/coontec/event/133762", "쿤텍 AI 보안 세미나", "2026-10-27", "신규", "2026-09-24"),
    ("3e7f4e59002281658313f9c872d9b140", "https://onoffmix.com/event/349878", "스마트에너지플러스 2026", "2026-10-28", "신규", "2026-09-26"),
    ("3e4f4e590022812a850cea10a5cb2891", "https://onoffmix.com/event/349798", "생성형 AI 기반 제조품질 문제해결 실무과정", "2026-10-28", "신규", "2026-09-24"),
    ("3e4f4e59002281b0bd49cf29c29f2bda", "https://event-us.kr/kecft/event/132057", "[10.28] AI 기반 의료·바이오 R&D", "2026-10-28", "신규", "2026-09-24"),
    ("3e4f4e59002281dfbcb3c21a767a2850", "https://event-us.kr/seminarhub/event/128069", "AI 데이터센터(AIDC) 개발사업", "2026-10-28", "신규", "2026-09-24"),
    ("3e4f4e59002281b1bf34f932e7d9a0b9", "https://event-us.kr/peoplus/event/134972", "AI 시대의 지능형 사이버 보안 전략", "2026-10-28", "신규", "2026-09-24"),
    ("3e4f4e59002281eaae6bd430acb92ce0", "https://event-us.kr/ITwkuIC3lSfi/event/111267", "트렌드쇼2026 : AI와의 경쟁", "2026-10-28", "신규", "2026-09-23"),
    ("3e4f4e5900228102924dfd37dcfc6726", "https://www.showala.com/ex/ex_detail.php?idx=3311", "BATTERY ASIA SHOW 2026", "2026-10-28", "기존", "2026-09-23"),
    ("3e4f4e59002281a2bd94d470ec4f4eb7", "https://event-us.kr/insadream/event/126515", "Gemini 기반 실무 AI 활용 기본교육", "2026-10-29", "신규", "2026-09-24"),
    ("3e4f4e59002281b69213cba7dc3eba63", "https://event-us.kr/hrdkitanet/event/135299", "Claude AI로 완성하는 데이터·API 활용", "2026-10-30", "신규", "2026-09-24"),
    ("3e4f4e5900228162a414d8c40fdf166c", "https://event-us.kr/gipakhp/event/135617", "(10/30) 고양산업진흥원 K-하이테크플랫폼", "2026-10-30", "신규", "2026-09-24"),
    ("3e4f4e590022818b9caaf5971e3ed8c7", "https://event-us.kr/npit/event/133774", "Tech Bridge 2026", "2026-10-30", "신규", "2026-09-24"),
    ("3e4f4e59002281deae12d76e59a6f6cd", "https://event-us.kr/hanbitacademy/event/135852", "[한빛아카데미] 채점·피드백 에이전트", "2026-10-31", "신규", "2026-09-24"),
    ("3e4f4e59002281858b43ee796104819b", "https://event-us.kr/insadream/event/133728", "AI를 활용한 손쉬운 교육효과 측정", "2026-11-02", "신규", "2026-09-24"),
    ("3e4f4e5900228104b0f8f3f137b3b884", "http://www.aiotkorea.or.kr/2026/kor/about/overview.asp", "AIoT Korea Exhibition & Conference 2026", "2026-11-03", "신규", "2026-09-23"),
    ("3e4f4e5900228130b516c9e56ec3da1c", "https://event-us.kr/tradeedu03/event/135916", "초보자를 위한 AI 업무 활용 단기속성", "2026-11-04", "신규", "2026-09-24"),
    ("3e4f4e590022818984b3e538c609f0c0", "https://event-us.kr/AIoTWeek/event/135387", "2026 AIoT 국제컨퍼런스", "2026-11-04", "신규", "2026-09-24"),
    ("3e4f4e59002281ec9238ea649be1b138", "https://event-us.kr/seminarhub/event/134890", "하루만에 끝내는 AI 에이전트 실무", "2026-11-04", "신규", "2026-09-24"),
    ("3e4f4e59002281f1a02ef528b4ec598e", "https://www.robotworld.or.kr/", "2026 로보월드", "2026-11-04", "기존", "2026-09-23"),
    ("3e4f4e59002281f29fdbdbac85671f65", "https://event-us.kr/insadream/event/135170", "AI로 10배 빨라지는 현장 리더 실무 혁신", "2026-11-06", "신규", "2026-09-24"),
    ("3e4f4e5900228140b950f2a8635bb106", "https://event-us.kr/insadream/event/128037", "AI 전환기 경영관리 GPT 실무역량", "2026-11-09", "신규", "2026-09-24"),
    ("3e4f4e590022814a9fa3de71211127be", "https://event-us.kr/tradeedu03/event/135935", "AI와 함께하는 기초 무역서류", "2026-11-11", "신규", "2026-09-24"),
    ("3e4f4e59002281b0b1beeb98b29d7f51", "https://event-us.kr/seminarhub/event/135486", "K-배터리 초격차 전략", "2026-11-11", "신규", "2026-09-24"),
    ("3e4f4e59002281408ea1d21aafc3d59f", "https://event-us.kr/ksnconf/event/112325", "Korean SPICE Network International Conference", "2026-11-12", "기존", "2026-09-23"),
    ("3e4f4e5900228193974cd8ba33ee1f45", "https://event-us.kr/insadream/event/133214", "AI 활용 프로젝트관리[PM]", "2026-11-13", "신규", "2026-09-24"),
    ("3e4f4e590022819c99dbc403646fc6b7", "https://onoffmix.com/event/349841", "생성형 AI를 활용한 사업계획서 작성", "2026-11-18", "신규", "2026-09-24"),
    ("3e4f4e59002281b1ac9fed744ca4a179", "https://www.ksae.org/workshop/202602/", "2026 한국자동차공학회 추계학술대회 및 전시회", "2026-11-18", "기존", "2026-09-23"),
    ("3e4f4e5900228168982cfdbb9c03c4f0", "https://event-us.kr/seminarhub/event/134914", "2026 한국RE100컨퍼런스", "2026-11-26", "신규", "2026-09-24"),
    ("3e7f4e59002281de8afaf6f54a7e5162", "https://event-us.kr/wta/event/134589", "재직자를 위한 무역·AI 융합 혁신 교육", "2026-12-08", "신규", "2026-09-24"),
    ("3e4f4e59002281c4807af47583fe35a9", "https://event-us.kr/kecft/event/130457", "[12.10] XR 디바이스와 피지컬 AI", "2026-12-10", "신규", "2026-09-24"),
    ("3e4f4e5900228189ad57d240910177f1", "https://onoffmix.com/event/343884", "[전액 무료] 2026 인천 AI디지털배움터", "2026-12-11", "신규", "2026-09-24"),
    ("3e8f4e590022808a9e16fd881189b7de", "", "", "", None, ""),
]
have = {r["id"] for r in rows}
for i, u, t, s, st, fs in P2:
    if i not in have:
        rows.append({"id": i, "url": u, "title": t, "start": s, "end": None, "status": st, "fs": fs})
json.dump(rows, open(os.path.join(OUT, "notion_rows.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
from collections import Counter
print(len(rows), Counter(r["status"] for r in rows), Counter(r["fs"] for r in rows))
print("끝난 행:", [(r["id"], r["title"][:30], r["end"]) for r in rows if r["end"] and r["end"] < "2026-10-03"])
print("빈 행:", [r["id"] for r in rows if not r["title"]])
