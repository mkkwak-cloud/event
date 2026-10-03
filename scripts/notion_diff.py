"""data/events.json 과 Notion 기존 행(data/notion_sync/notion_rows.json)을 비교해 할 일을 계산한다.

출력(data/notion_sync/): to_create.json, to_convert.json(신규→기존), to_move.json(종료 정리)
"""
import difflib
import json
import os
import re
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "notion_sync")
TODAY = date.today().isoformat()


def nt(s):
    s = re.sub(r"\\(.)", r"\1", s or "")
    s = re.sub(r"\[([^\]]*)\]\(http[^)]*\)", r"\1", s)  # 노션이 만든 링크 문법
    return re.sub(r"[\s\[\]()【】「」『』<>~|·‧·\-_:：,.'\"“”‘’!?]", "", s).lower()


def nu(u):
    u = (u or "").strip().split("#")[0].rstrip("/")
    return re.sub(r"^https?://(www\.)?", "", u).lower()


def evid(u):
    m = re.search(r"/event/(\d+)", u or "")
    return m.group(1) if m else None


rows = json.load(open(os.path.join(OUT, "notion_rows.json"), encoding="utf-8"))
events = json.load(open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8"))["events"]

by_url = {nu(r["url"]): r for r in rows if r["url"]}
by_evid = {evid(r["url"]): r for r in rows if evid(r["url"])}


def similar(a, b):
    """제목이 같은 행사로 볼 만큼 비슷한가 (a, b는 정리된 제목)."""
    if not a or not b:
        return False
    if difflib.SequenceMatcher(None, a, b).ratio() >= 0.85:
        return True
    m = difflib.SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b)).size
    return m >= 10 and m / min(len(a), len(b)) >= 0.6


def match(e):
    r = by_url.get(nu(e["url"]))
    if r:
        return r, "url"
    if evid(e["url"]) and evid(e["url"]) in by_evid:
        return by_evid[evid(e["url"])], "id"
    tn = nt(e["title"])
    for r in rows:
        if r["start"] == e["start"] and similar(tn, nt(r["title"])):
            return r, "title"
    # 제목에 [MM.DD]가 있는데 시작일이 그 날짜와 다르면 시작일이 잘못 잡힌 것 -> 날짜 무시하고 비교
    m = re.match(r"\s*\[(\d{1,2})\.(\d{1,2})\]", e["title"])
    if m and e["start"][5:] != f"{int(m.group(1)):02d}-{int(m.group(2)):02d}":
        for r in rows:
            if similar(tn, nt(r["title"])):
                return r, "제목날짜"
    return None, None


# 이름은 다르지만 Notion에 이미 있는 같은 행사로 직접 판단해 건너뛴 것 (2026-10-03)
MANUAL_DUP = {
    "exco.co.kr/schedule/schedule_view.html?code=p_pv": "FIX 2026 (대한민국 미래모빌리티엑스포)",
    "event-us.kr/amxpo/event/130394": "AMXPO 2026 (아시아 기계·제조산업전)",
    "2026 아시아 기계&제조 산업전": "AMXPO 2026 (킨텍스)",
    "onoffmix.com/event/349960": "엠클라우드브리지 Ai 365 세미나",
    "onoffmix.com/event/349302": "하루만에 끝내는 AI 에이전트 실무 (세미나허브)",
}

create, dup = [], []
for e in events:
    r, how = match(e)
    if not r:
        k = next((k for k in MANUAL_DUP if k in nu(e["url"]) or k in e["title"]), None)
        if k:
            r, how = {"title": MANUAL_DUP[k]}, "수동중복"
    if r:
        dup.append((e, r, how))
        continue
    # 이번 수집분 안의 중복(같은 시작일에 제목이 비슷한 것)은 먼저 나온 것만
    twin = next((c for c, _, _ in create if c["start"] == e["start"] and similar(nt(c["title"]), nt(e["title"]))), None)
    if twin:
        dup.append((e, {"title": twin["title"]}, "수집분중복"))
    else:
        create.append((e, None, None))

# 종료 정리: 종료일이 오늘보다 이전인 행
to_move = [r["id"] for r in rows if r["end"] and r["end"] < TODAY]
moved = set(to_move)
# 신규 -> 기존: 상태가 신규이고 최초발견일이 7일 이상 지난 행 (정리 대상 제외)
to_convert = []
for r in rows:
    if r["status"] == "신규" and r["fs"] and r["id"] not in moved:
        if (date.fromisoformat(TODAY) - date.fromisoformat(r["fs"])).days >= 7:
            to_convert.append(r["id"])

json.dump(to_move, open(os.path.join(OUT, "to_move.json"), "w"), indent=0)
json.dump(to_convert, open(os.path.join(OUT, "to_convert.json"), "w"), indent=0)


def props(e):
    p = {
        "행사명": e["title"],
        "분야태그": json.dumps(e["tags"], ensure_ascii=False),
        "유형": e["notion_kind"],
        "date:시작일:start": e["start"], "date:시작일:is_datetime": 0,
        "date:종료일:start": e["end"] or e["start"], "date:종료일:is_datetime": 0,
        "장소": e["place"] or "",
        "온라인여부": e["online"] or "오프라인",
        "주최": e["host"] or "",
        "참가비": e["fee"] or "",
        "원문URL": e["url"],
        "date:수집일:start": TODAY, "date:수집일:is_datetime": 0,
        "date:최초발견일:start": e["first_seen"], "date:최초발견일:is_datetime": 0,
        "상태": "신규",
    }
    if e.get("deadline"):
        p["date:등록마감일:start"] = e["deadline"]
        p["date:등록마감일:is_datetime"] = 0
    return p


pages = [{"properties": props(e)} for e, _, _ in create]
for i in range(0, len(pages), 50):
    json.dump(pages[i:i + 50], open(os.path.join(OUT, f"to_create_{i // 50 + 1}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

print(f"오늘 {TODAY} | 이번 수집 {len(events)}건 | Notion 기존 {len(rows)}행")
print(f"추가 {len(create)}건 · 이미 있음 {len(dup)}건 (url {sum(h=='url' for *_, h in dup)}, 번호 {sum(h=='id' for *_, h in dup)}, 제목 {sum(h=='title' for *_, h in dup)}, 제목날짜 {sum(h=='제목날짜' for *_, h in dup)}, 수집분중복 {sum(h=='수집분중복' for *_, h in dup)})")
print(f"신규→기존 {len(to_convert)}건 · 종료정리 {len(to_move)}건")
print("--- 제목 유사로만 같다고 본 건(확인용)")
for e, r, h in dup:
    if h in ("title", "제목날짜", "수집분중복"):
        print("  ", h, "|", e["title"][:38], "|", r["title"][:38], e["start"])
print("--- 추가 대상")
for e, _, _ in create:
    print("  ", e["start"], e["notion_kind"], e["title"][:50], "|", e["url"][:60])
