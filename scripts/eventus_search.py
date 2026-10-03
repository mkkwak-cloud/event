"""이벤터스(event-us.kr) 행사 전수 검색.

이벤터스 검색 화면은 JS가 공개 검색 API(api.event-us.kr/api/v1/engine/search)를
호출해 목록을 그리므로, 페이지 크롤링 대신 API를 직접 페이지네이션한다.

사용법: python eventus_search.py [--days 92] [--out eventus_events.json]
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.event-us.kr/api/v1/engine/search"
KST = timezone(timedelta(hours=9))

# 분야태그 -> 검색어
KEYWORDS = {
    "자율주행": ["자율주행", "ADAS"],
    "SDV": ["SDV", "소프트웨어 중심 자동차", "차량 소프트웨어", "모빌리티", "자동차"],
    "전기차": ["전기차", "EV"],
    "배터리": ["배터리", "이차전지", "2차전지", "전고체", "리튬이온", "BMS", "배터리 관리 시스템",
             "양극재", "음극재", "고체 전해질", "분리막", "폐배터리", "배터리 재활용", "사용후 배터리",
             "열폭주", "배터리 안전", "EV 충전", "충전 인프라", "ESS"],
    "수소차": ["수소차", "수소전기차", "수소 모빌리티", "연료전지", "FCEV", "수소충전소", "수소 충전",
             "수소버스", "수소트럭", "수소경제", "수소 산업", "H2 MEET"],
    "E/E아키텍처": ["E/E 아키텍처", "전장"],
    "ECU": ["ECU"],
    "AUTOSAR": ["AUTOSAR"],
    "차량용반도체": ["차량용 반도체", "반도체"],
    "ASPICE": ["ASPICE", "SPICE"],
    "ISO26262": ["ISO 26262", "기능안전"],
    "SOTIF": ["SOTIF"],
    "ISO21434": ["ISO 21434", "자동차 사이버보안"],
    "CMMI": ["CMMI"],
    "생성형AI": ["생성형 AI", "AI", "LLM", "AI 에이전트"],
    "제조AI": ["제조 AI", "스마트팩토리", "피지컬 AI"],
    "디지털전환": ["디지털 전환", "DX"],
    "AX전환": ["AX", "AI 전환"],
}


# 검색 API는 "제조 AI"를 "AI"만 있어도 매칭하므로, 분야태그는 본문 정규식으로 다시 판정한다.
TAG_PATTERNS = {
    "자율주행": r"자율주행|ADAS",
    "SDV": r"SDV|소프트웨어\s*중심\s*자동차|차량\s*SW|차량용\s*소프트웨어|모빌리티|자동차",
    "전기차": r"전기차|\bEV\b",
    "배터리": (r"배터리|[이2]차\s*전지|전고체|리튬\s*이온|\bBMS\b|양극재|음극재|고체\s*전해질|전해액|분리막|"
             r"열\s*폭주|\bLFP\b|\bNCM\b|소듐\s*이온|나트륨\s*이온|\bESS\b|에너지\s*저장|"
             r"(?:EV|전기차)\s*충전|충전\s*인프라|충전기"),
    # '수소' 단독은 수소수·수소 가습기 등이 걸리므로 모빌리티·에너지 산업 맥락과 함께만 인정
    "수소차": (r"수소\s*(?:전기)?차|수소\s*(?:모빌리티|충전|버스|트럭|트램|선박|열차|연료전지|경제|산업|에너지|"
             r"생태계|밸류체인|엑스포|박람회|전시|포럼|컨퍼런스|기술)|연료\s*전지|\bFCEV\b|\bH2\s*MEET\b|"
             r"\bWHE\b|넥쏘"),
    "E/E아키텍처": r"E/E|전장|차량\s*이더넷|10BASE-T1S",
    "ECU": r"\bECU\b",
    "AUTOSAR": r"AUTOSAR",
    "차량용반도체": r"반도체",
    "ASPICE": r"A?SPICE",
    "ISO26262": r"26262|기능\s*안전|Functional\s*Safety",
    "SOTIF": r"SOTIF",
    "ISO21434": r"21434|CSMS|차량\s*사이버",
    "CMMI": r"CMMI",
    "생성형AI": r"생성형|LLM|GPT|AI\s*에이전트|에이전틱",
    "제조AI": r"제조\s*AI|스마트\s*팩토리|피지컬\s*AI|산업\s*AI",
    "디지털전환": r"디지털\s*전환|\bDX\b",
    "AX전환": r"\bAX\b|AI\s*전환|AI\s*트랜스포메이션",
    # 위 세부 분야에 안 걸리는 일반 AI 행사 (관련도 가중치 낮음)
    "AI일반": r"인공지능|(?<![A-Za-z])AI(?![A-Za-z])|딥러닝|머신러닝|AIoT",
}
KEEP_TYPES = {"강연/세미나", "박람회/페어", "공연/전시", "학술회의", "컨벤션", "워크샵/클리닉"}
DROP_CATEGORIES = {"디자인/영상", "마케팅", "라이프", "관광/여행", "예술", "게임", "의료/의학", "커리어"}
MAX_SPAN_DAYS = 14  # 이보다 긴 건 장기 수강 과정으로 보고 제외


def is_relevant(ev):
    if ev["유형_원본"] not in KEEP_TYPES or ev["카테고리"] in DROP_CATEGORIES:
        return False
    if ev["시작일"] and ev["종료일"]:
        span = (datetime.fromisoformat(ev["종료일"]) - datetime.fromisoformat(ev["시작일"])).days
        if span >= MAX_SPAN_DAYS:
            return False
    text = " ".join([ev["행사명"] or "", ev["설명"] or "", " ".join(ev["태그"] or [])])
    ev["분야태그"] = [t for t, p in TAG_PATTERNS.items() if re.search(p, text, re.I)]
    return bool(ev["분야태그"])


def search(query, frm, to, page, size=100):
    body = {
        "query": query,
        "page": {"current": page, "size": size},
        "filters": {"all": [
            {"state": "Start"},
            {"disclosure_status": "open"},
            {"is_ignore": "false"},
            {"start_date": {"from": frm.isoformat(), "to": to.isoformat()}},
        ]},
        "sort": [{"_score": "desc"}, {"id": "desc"}],
    }
    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json", "referer": "https://event-us.kr/",
                 "user-agent": "Mozilla/5.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def raw(doc, key):
    v = doc.get(key) or {}
    return v.get("raw")


def to_kst_date(s):
    if not s:
        return None
    return datetime.fromisoformat(s).astimezone(KST).date().isoformat()


def gather(days=92, log=sys.stderr):
    """키워드 전체를 페이지네이션해 관련 행사만 돌려준다."""
    now = datetime.now(KST)
    until = now + timedelta(days=days)
    events = {}

    for tag, queries in KEYWORDS.items():
        for q in queries:
            page = 1
            while True:
                res = search(q, now, until, page)
                for d in res["results"]:
                    eid = raw(d, "id")
                    ev = events.setdefault(eid, {
                        "id": eid,
                        "행사명": raw(d, "title"),
                        "유형_원본": raw(d, "event_type"),
                        "카테고리": raw(d, "category"),
                        "시작일": to_kst_date(raw(d, "start_date")),
                        "종료일": to_kst_date(raw(d, "close_date")),
                        "등록마감일": to_kst_date(raw(d, "register_due_date")),
                        "장소": raw(d, "full_address") or raw(d, "place"),
                        "온라인": raw(d, "event_system_type"),
                        "주최": raw(d, "app_title"),
                        "최소참가비": raw(d, "min_money"),
                        "태그": raw(d, "tags"),
                        "설명": raw(d, "description"),
                        "원문URL": f"https://event-us.kr/{raw(d, 'subdomain')}/event/{eid}",
                        "분야태그": [],
                        "검색어": [],
                    })
                    if tag not in ev["분야태그"]:
                        ev["분야태그"].append(tag)
                    if q not in ev["검색어"]:
                        ev["검색어"].append(q)
                meta = res["meta"]["page"]
                print(f"[{tag}] '{q}' page {page}/{meta['total_pages']} "
                      f"({meta['total_results']}건)", file=log)
                if page >= meta["total_pages"]:
                    break
                page += 1

    out = sorted((e for e in events.values() if is_relevant(e)), key=lambda e: e["시작일"] or "")
    print(f"검색 결과 {len(events)}건 중 관련 행사 {len(out)}건", file=log)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=92)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "eventus_events.json"))
    args = ap.parse_args()
    out = gather(args.days)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
