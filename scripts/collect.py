"""자동차·전장·AI/AX 행사 주간 수집기.

수집처는 세 종류다.
  - api      : 이벤터스 공개 검색 API (eventus_search.py)
  - onoffmix : 온오프믹스 검색 결과 HTML 파싱
  - firecrawl: 그 밖의 행사 목록 페이지를 firecrawl JSON 추출로 읽음

결과는 data/events.json (대시보드·Notion 동기화 입력)과
data/seen.json (행사별 최초 발견일)에 저장한다.

사용법: python collect.py [--days 122] [--only 소스명,소스명] [--skip-firecrawl] [--force-all]
"""
import argparse
import hashlib
import html as htmllib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

import eventus_search
from direct_parsers import DIRECT_PARSERS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ---------------------------------------------------------------- 수집처 목록
# group: 대시보드 필터에 쓰는 기관 구분
FIRECRAWL_SOURCES = [
    # 전시장
    ("코엑스", "전시장", "https://www.coex.co.kr/event/full-schedules/"),
    ("킨텍스", "전시장", "https://www.kintex.com/web/ko/event/clist.do"),
    ("벡스코", "전시장", "https://www.bexco.co.kr/kor/CMS/EventScheduleMgr/list.do?mCode=MN214"),
    ("엑스코", "전시장", "https://www.exco.co.kr/schedule/sub01.html"),
    ("수원컨벤션센터", "전시장", "https://www.scc.or.kr/events-3/"),
    # 자동차 기관·협회
    ("KATECH 교육", "자동차기관", "https://edu.katech.re.kr/core/?cid=24"),
    ("KATECH", "자동차기관", "https://www.katech.re.kr"),
    ("KAMA", "자동차기관", "https://www.kama.or.kr"),
    ("KSAE", "자동차기관", "https://www.ksae.org"),
    # 홈페이지 공지("~오픈")는 접수시작일이 개최일로 잘못 추출되는 경우가 있어,
    # 정확한 개최일이 있는 연간 일정 페이지를 별도 소스로 함께 수집한다
    ("KSAE 연간일정", "자동차기관", "https://www.ksae.org/bbs/?code=schedule&category=A&mode=tlist"),
    # 자동차·AI 학회
    ("대한기계학회", "학회", "https://ksme.or.kr/conference/conference01_1.asp?AC=3&top_param=1&sub_param=4"),
    ("한국자동차공학한림원", "학회", "https://www.kaae.kr/"),
    ("한국자동차모빌리티안전학회", "학회", "https://www.kasa.kr/"),
    ("한국정보과학회", "학회", "https://www.kiise.or.kr/"),
    ("한국인공지능학회", "학회", "https://aiassociation.kr/"),
    # AI·SW 협회
    ("KOSA 행사", "AI·SW협회", "https://www.sw.or.kr/site/sw/ex/board/List.do?cbIdx=292&cateCd=NTC_C002"),
    ("KOSA 교육", "AI·SW협회", "https://www.sw.or.kr/site/sw/edu/selectEduListGallery.do"),
    ("한국인공지능협회", "AI·SW협회", "https://koraia.org/default/mp5/sub2.php"),
    ("KIoT", "AI·SW협회", "https://www.kiot.or.kr/cms/list?CM_CODE=89qcz4"),
    # 경제단체
    ("대한상공회의소", "경제단체", "https://www.korcham.net/nCham/Service/Event/appl/KcciNewsList.asp"),
    ("한국경제인협회", "경제단체", "https://www.fki.or.kr/kor/news/notice.do"),
    ("FKI 세미나", "경제단체", "https://seminar.fki.or.kr"),
    # 언론사 컨퍼런스
    ("전자신문", "언론사", "https://conference.etnews.com/conf_list.html?t=ing"),
    ("파이낸셜뉴스", "언론사", "https://event.fnnews.com/"),
    ("디지털데일리", "언론사", "https://www.ddaily.co.kr/seminar"),
    ("아이뉴스24", "언론사", "https://www.inews24.com/"),
    ("테크M", "언론사", "https://www.techm.kr/"),
    # 정부·공공기관: 대부분 사업 공고라 행사 수율이 낮아 격주 수집
    ("NIPA", "공공기관", "https://www.nipa.kr/home/2-1", "biweekly"),
    ("NIA", "공공기관", "https://www.nia.or.kr/site/nia_kor/ex/bbs/List.do?cbIdx=99835", "biweekly"),
    ("IITP", "공공기관", "https://www.iitp.kr", "biweekly"),
    ("KIAT", "공공기관", "https://www.kiat.or.kr/front/user/main.do", "biweekly"),
    ("KEIT", "공공기관", "https://www.keit.re.kr/menu.es?mid=a10301010000", "biweekly"),
    ("스마트제조혁신추진단", "공공기관", "https://www.smart-factory.kr", "biweekly"),
]
# 목록 URL을 못 찾았거나 차단되어 꺼 둔 곳 (0건 또는 403):
#   GEP 국내전시(gep.or.kr), 페스타(festa.io), ZDNet Korea(403)

ONOFFMIX_QUERIES = ["자율주행", "SDV", "전기차", "배터리", "이차전지", "전고체", "BMS", "폐배터리",
                    "충전 인프라", "ESS", "수소차", "수소 모빌리티", "연료전지", "수소충전소", "자동차", "모빌리티", "반도체",
                    "기능안전", "AUTOSAR", "ASPICE", "사이버보안", "생성형 AI", "AI 에이전트",
                    "제조 AI", "피지컬 AI", "스마트팩토리", "디지털 전환", "AX", "LLM"]

# ---------------------------------------------------------------- 분류 규칙
TAG_PATTERNS = eventus_search.TAG_PATTERNS
AUTO_TAGS = {"자율주행", "SDV", "전기차", "배터리", "수소차", "E/E아키텍처", "ECU", "AUTOSAR", "차량용반도체",
             "ASPICE", "ISO26262", "SOTIF", "ISO21434", "CMMI"}

# 행사 성격: 위에서부터 먼저 맞는 것을 쓴다
ACAD_PATTERN = r"학술대회|학술회의|학술발표회"
CONF_PATTERN = r"컨퍼런스|콘퍼런스|Conference|포럼|Forum|서밋|Summit|심포지엄|\bCON\b"
KIND_RULES = [
    ("학술대회", ACAD_PATTERN),
    ("전시회", r"전시회|박람회|엑스포|EXPO|\bSHOW\b|\bFair\b|페어|산업전|대전\b|쇼\b"),
    ("컨퍼런스·포럼", CONF_PATTERN),
    ("웨비나", r"웨비나|Webinar|온라인\s*세미나|라이브"),
    ("세미나명시", r"세미나"),  # 제목에 '세미나'가 명시되면 '교육' 단어가 섞여도 세미나 (제목만 봄)
    ("교육", r"교육|과정|수강|캠프|Training|실습|아카데미|워크숍|워크샵|강좌|부트캠프|클래스|Class"),
    ("세미나", r"."),  # 설명회·상담회·공청회 등도 여기로 접힌다
]
KIND_TO_NOTION = {"학술대회": "컨퍼런스", "전시회": "전시회", "컨퍼런스·포럼": "컨퍼런스",
                  "웨비나": "웨비나", "교육": "교육", "세미나": "세미나"}


# 업계 행사가 아닌 구직·국비과정·소비자 대상 항목
NOISE = re.compile(
    r"취업|채용|구직|이직|면접|자소서|국비|부트캠프|훈련생|수강생\s*모집|교육생\s*모집|공모전|"
    r"K-Digital|수당|청년취업|개강|생활기술|숏폼|영상편집|웹디자인|퍼블리셔|UI/UX|대외활동|서포터즈|"
    r"경진대회|챌린지|공모|\b대회\b|참가기업\s*모집|기업\s*모집|수요조사|소상공인|시니어|아두이노|"
    r"제미나이.*특강|브랜딩|인사노무|노사관계|MZ세대|온보딩|투자자|혁신대상|"
    r"참관객?\s*(사전)?\s*등록|관람객?\s*(사전)?\s*등록|"  # 본행사와 별도로 잡히는 참관(관람) 등록 안내 게시물
    r"IR\s*피칭|IR\s*Day|데모\s*데이|피칭\s*데이|"  # 단순 IR·투자 피칭 행사
    r"(?i:신청\s*open)|참가\s*신청\s*오픈|"  # 단순 참가신청 안내(행사 자체 정보 없음)
    r"[<>|]\s*/")  # 파싱이 깨진 제목
MAX_SPAN_DAYS = 14
# AI 관련 '교육'·'세미나' 중 업계 기술 행사가 아닌 직무교육류 (자동차 분야 태그가 붙은 행사는 제외 대상 아님)
EDU_EXCLUDE = re.compile(r"마케팅|HRD|인적자원|디자인|재직자|자격증|자격\s*취득", re.I)


def classify_kind(title, hint="", online=""):
    text = f"{title} {hint}"
    for kind, pat in KIND_RULES:
        if kind == "세미나명시":
            if re.search(pat, title):
                return "세미나"
            continue
        if re.search(pat, text, re.I):
            if kind == "세미나" and online == "온라인":
                return "웨비나"
            return kind
    return "세미나"


def tag_event(title, desc=""):
    text = f"{title} {desc}"
    # 'AI일반'은 범위가 넓어 설명문까지 보면 잡음이 많으므로 제목만 본다
    return [t for t, p in TAG_PATTERNS.items()
            if re.search(p, title if t == "AI일반" else text, re.I)]


# 전시장 일정은 행사명이 짧아(예: "KES 2026") 세부 키워드가 없으므로 넓은 기술 키워드로 판정
EXPO_BROAD = [
    ("AI일반", r"인공지능|\bAI\b"),
    ("제조AI", r"제조|기계|소재|로봇|자동화"),
    ("차량용반도체", r"반도체|전자전|전자\s*부품"),
    ("디지털전환", r"ICT|디지털|스마트|전자|IoT|소프트웨어|\bSW\b"),
]
EXPO_EXCLUDE = re.compile(r"식품|음식|푸드|FOOD|웨딩|유학|재테크|부동산|집코노미|캠핑|반려|펫|베이비|육아|뷰티|축제|관광|주류|커피|카페")

# 자동차기관·학회 소스는 그 자체가 자동차·AI 분야로 선별된 곳이라, 행사명이
# 약어·일반명(예: "K-CRASH", "iTIP 2026", "OO 학술대회")뿐이라 키워드가 안 걸려도
# 무관한 행사로 보지 않는다. 특정 세부 키워드가 없을 때만 소스별 기본 분야를 붙인다.
SOURCE_DEFAULT_TAG = {
    "KATECH 교육": "SDV", "KATECH": "SDV", "KAMA": "SDV", "KSAE": "SDV", "KSAE 연간일정": "SDV",
    "대한기계학회": "SDV", "한국자동차공학한림원": "SDV", "한국자동차모빌리티안전학회": "SDV",
    "한국정보과학회": "AI일반", "한국인공지능학회": "AI일반",
}


def tag_expo(title):
    if EXPO_EXCLUDE.search(title):
        return []
    return [t for t, p in EXPO_BROAD if re.search(p, title, re.I)]


def norm_key(title, start):
    t = re.sub(r"\[.*?\]|\(.*?\)|[^0-9A-Za-z가-힣]", "", title).lower()
    return f"{t[:20]}|{start or ''}"


def parse_date(s):
    if not s:
        return None
    m = re.search(r"(20\d{2})[-./년\s]+(\d{1,2})[-./월\s]+(\d{1,2})", str(s))
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


# ---------------------------------------------------------------- HTTP 도우미
def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def firecrawl_key():
    key = os.environ.get("FIRECRAWL_API_KEY")
    if key:
        return key
    cfg = json.load(open(os.path.expanduser("~/.claude.json"), encoding="utf-8"))
    for proj in cfg.get("projects", {}).values():
        env = proj.get("mcpServers", {}).get("firecrawl", {}).get("env", {})
        if env.get("FIRECRAWL_API_KEY"):
            return env["FIRECRAWL_API_KEY"]
    raise RuntimeError("FIRECRAWL_API_KEY를 찾을 수 없습니다")


EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {"events": {"type": "array", "items": {"type": "object", "properties": {
        "title": {"type": "string"},
        "start_date": {"type": "string"},
        "end_date": {"type": "string"},
        "registration_deadline": {"type": "string"},
        "location": {"type": "string"},
        "online": {"type": "string"},
        "host": {"type": "string"},
        "fee": {"type": "string"},
        "detail_url": {"type": "string"},
        "kind": {"type": "string"},
    }}}},
}


def firecrawl_extract(url, key, today, retries=3):
    prompt = (
        f"오늘은 {today.isoformat()}입니다. 이 페이지에 실제로 적혀 있는 행사 중 "
        "전시회·박람회·컨퍼런스·포럼·세미나·설명회·교육·워크숍·웨비나만 추출하세요. "
        "오늘 이전에 끝난 행사, 채용·입찰·결과발표 같은 일반 공지는 제외합니다. "
        "날짜는 YYYY-MM-DD 형식으로 쓰고, 연도가 없으면 오늘 이후의 가장 가까운 연도를 씁니다. "
        "페이지에 없는 정보는 추측하지 말고 빈 문자열로 둡니다. "
        "title은 페이지 표기를 그대로, detail_url은 절대 URL로 씁니다. "
        "online은 오프라인/온라인/하이브리드 중 하나입니다."
    )
    body = json.dumps({
        "url": url,
        "formats": ["markdown", {"type": "json", "prompt": prompt, "schema": EXTRACT_SCHEMA}],
        "onlyMainContent": False,
        "waitFor": 2500,
        "timeout": 90000,
    }).encode("utf-8")
    for attempt in range(retries):
        req = urllib.request.Request(
            "https://api.firecrawl.dev/v2/scrape", data=body, method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=150) as r:
                res = json.load(r)
            d = res.get("data", {})
            return d.get("json", {}).get("events", []) or [], d.get("markdown", "") or ""
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(20 * (attempt + 1))
                continue
            raise


# ---------------------------------------------------------------- 수집기
def from_eventus(days, log):
    out = []
    for e in eventus_search.gather(days, log=log):
        online = {"offline": "오프라인", "online": "온라인", "hybrid": "하이브리드"}.get(e["온라인"], "")
        m = e["최소참가비"] or 0
        out.append({
            "title": e["행사명"].strip(), "start": e["시작일"], "end": e["종료일"],
            "deadline": e["등록마감일"], "place": e["장소"] or ("온라인" if online == "온라인" else ""),
            "online": online, "host": e["주최"] or "",
            "fee": "무료" if not m else ("유료" if m <= 1000 else f"{int(m):,}원~"),
            "url": e["원문URL"], "source": "이벤터스", "group": "행사플랫폼",
            "kind_hint": e["유형_원본"], "desc": e["설명"] or "",
        })
    return out


def from_onoffmix(days, log):
    out, seen = [], set()
    for q in ONOFFMIX_QUERIES:
        url = "https://onoffmix.com/event/main?s=" + urllib.parse.quote(q)
        try:
            h = http_get(url)
        except Exception as ex:
            print(f"  온오프믹스 '{q}' 실패: {ex}", file=log)
            continue
        n = 0
        for art in re.findall(r'<article class="event_area[^"]*">(.*?)</article>', h, re.S):
            m_id = re.search(r'href="/event/(\d+)"', art)
            m_title = re.search(r'<h5 class="title[^"]*" title="([^"]+)"', art)
            m_date = re.search(r'<div class="list_date_place">.*?<span class="date">(.*?)</span>', art, re.S)
            if not (m_id and m_title and m_date) or m_id.group(1) in seen:
                continue
            if "종료된 이벤트" in art and "end_layer" in art and "before_closing" not in art:
                continue
            seen.add(m_id.group(1))
            dates = re.findall(r"20\d{2}\.\d{1,2}\.\d{1,2}", m_date.group(1))
            start = parse_date(dates[0]) if dates else None
            end = parse_date(dates[-1]) if dates else start
            place = re.search(r'<span class="place">(.*?)</span>', art, re.S)
            cat = re.search(r'<span class="category_type">(.*?)</span>', art)
            pay = re.search(r'<span class="payment_type[^"]*">(.*?)</span>', art)
            tags = " ".join(re.findall(r'<span class="tag"[^>]*>(.*?)</span>', art))
            place_txt = htmllib.unescape(place.group(1)).strip() if place else ""
            out.append({
                "title": htmllib.unescape(m_title.group(1)).strip(),
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None, "deadline": None,
                "place": place_txt, "online": "온라인" if "온라인" in place_txt else "오프라인",
                "host": "", "fee": pay.group(1).strip() if pay else "",
                "url": f"https://onoffmix.com/event/{m_id.group(1)}",
                "source": "온오프믹스", "group": "행사플랫폼",
                "kind_hint": cat.group(1) if cat else "", "desc": htmllib.unescape(tags),
            })
            n += 1
        print(f"  온오프믹스 '{q}': {n}건", file=log)
    return out


# scc.or.kr(수원컨벤션센터)는 firecrawl의 LLM JSON 추출이 호출마다 6~11건으로
# 들쭉날쭉하게 누락시킨다(같은 페이지의 markdown에는 항상 전체 목록이 규칙적인
# 카드 형식으로 들어있음). 그 markdown을 직접 정규식으로 파싱해 누락 없이 뽑는다.
CARD_MD_RE = re.compile(
    r"##\s*\[([^\]]+)\]\(([^)]+)\)\s*\n+"
    r"(\d{4}-\d{2}-\d{2})(?:\s*~\s*(\d{4}-\d{2}-\d{2}))?\s*\n+"
    r"(?:장소\s*:\s*([^\n]*)\n+)?"
    r"(?:주최/주관\s*:\s*([^\n]*))?"
)
CARD_KIND_RE = re.compile(r"(전시회|컨벤션|컨퍼런스|포럼|세미나|교육|축제|이벤트|강연|공연)")


def parse_card_markdown(md, base_url):
    out = []
    for m in CARD_MD_RE.finditer(md):
        title, url, start, end, place, host = m.groups()
        head = md[max(0, m.start() - 40):m.start()]
        km = CARD_KIND_RE.search(head)
        detail = url if url.startswith("http") else urllib.parse.urljoin(base_url, url)
        out.append({
            "title": title.strip(), "start_date": start, "end_date": end or start,
            "registration_deadline": "", "location": (place or "").strip(),
            "online": "오프라인", "host": (host or "").strip(),
            "fee": "", "detail_url": detail, "kind": km.group(1) if km else "",
        })
    return out


CARD_MARKDOWN_SOURCES = {"수원컨벤션센터"}


# 바뀐 곳만 읽기: 무료 시험(scripts/probe_free.py, 2026-10-03) 결과 받은 화면에 지난 행사 제목이
# 70% 이상 보이고 화면이 안정적인 곳만. 화면이 비어 있거나 제목이 안 보이는 곳은 바뀐 걸 놓칠 수 있어 뺐다.
CHANGE_DETECT = {
    "코엑스", "킨텍스", "KATECH 교육", "KATECH", "KSAE 연간일정", "대한기계학회",
    "한국자동차모빌리티안전학회", "한국인공지능학회", "KOSA 행사", "KOSA 교육", "한국인공지능협회",
    "KIoT", "대한상공회의소", "한국경제인협회", "전자신문", "파이낸셜뉴스", "디지털데일리",
    "NIPA", "NIA", "KIAT", "KEIT",
}
FULL_REFRESH_DAYS = 28  # 바뀐 게 없어도 이 기간마다 한 번은 firecrawl로 전부 새로 읽는다
HASH_PATH = os.path.join(DATA, "page_hash.json")


def page_fingerprint(url):
    """무료로 화면을 받아 스크립트·태그·공백을 뺀 글자의 지문을 돌려준다. 실패하면 None."""
    try:
        h = http_get(url)
    except Exception:
        return None
    if len(h) < 5000:  # 화면이 비어 있으면(자바스크립트로 그리는 곳) 감지 불가
        return None
    h = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", "", h)
    h = re.sub(r"(?s)<!--.*?-->", "", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return hashlib.sha1(re.sub(r"\s+", "", h).encode("utf-8")).hexdigest()


def http_get_auto(url, timeout=30):
    """화면이 선언한 글자 방식(charset)대로 해석해서 받는다 (euc-kr 등 대응)."""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        m = re.search(rb"charset=[\"']?([\w-]+)", raw[:4000])
        enc = m.group(1).decode() if m else (r.headers.get_content_charset() or "utf-8")
    try:
        return raw.decode(enc, "replace")
    except LookupError:
        return raw.decode("utf-8", "replace")


def direct_extract(name, url):
    """firecrawl 없이 무료로 읽는다. 화면을 못 받았거나 0건이면 None (→ firecrawl로 되돌아감)."""
    try:
        h = http_get_auto(url)
        items = DIRECT_PARSERS[name](h, url)
    except Exception:
        return None
    if not items:
        return None
    return items, re.sub(r"(?s)<[^>]+>", " ", h)


def from_firecrawl(sources, today, log, report, force=False):
    key = firecrawl_key()
    out = []
    hashes = json.load(open(HASH_PATH, encoding="utf-8")) if os.path.exists(HASH_PATH) else {}
    for name, group, url, *_ in sources:
        fp = None
        direct = direct_extract(name, url) if name in DIRECT_PARSERS else None
        if direct:
            print(f"  {name}: 무료 직접 읽기", file=log)
        if name in CHANGE_DETECT and not direct:
            fp = page_fingerprint(url)
            prev = hashes.get(name)
            if (fp and not force and prev and prev.get("hash") == fp
                    and (today - date.fromisoformat(prev["full"])).days < FULL_REFRESH_DAYS):
                report[name] = "변경 없음 (읽기 생략)"
                print(f"  {name}: 변경 없음 → firecrawl 생략", file=log)
                continue
        if direct:
            items, md = direct
        else:
            try:
                items, md = firecrawl_extract(url, key, today)
            except Exception as ex:
                print(f"  {name}: 실패 {ex}", file=log)
                report[name] = f"실패: {ex}"
                continue
        if name in CARD_MARKDOWN_SOURCES:
            # 페이지 상단의 달력형 위젯은 카드 목록에 없는 근시일 행사를 추가로 보여주므로
            # LLM 추출(들쭉날쭉하지만 달력도 읽음) 결과 중 카드 목록에 없는 것만 보탠다
            card_items = parse_card_markdown(md, url)
            seen_titles = {re.sub(r"\s+", "", c["title"]) for c in card_items}
            items = card_items + [it for it in items
                                   if re.sub(r"\s+", "", it.get("title") or "") not in seen_titles]
        md_norm = re.sub(r"\s+", "", md)
        kept = dropped = 0
        for it in items:
            title = (it.get("title") or "").strip()
            if not title:
                continue
            # 환각 방지: 제목 앞부분이 페이지 본문에 실제로 있어야 한다
            probe = re.sub(r"\s+", "", title)[:10]
            if md_norm and probe not in md_norm:
                dropped += 1
                continue
            s = parse_date(it.get("start_date"))
            e = parse_date(it.get("end_date")) or s
            dl = parse_date(it.get("registration_deadline"))
            detail = it.get("detail_url") or ""
            if detail and not detail.startswith("http"):
                detail = urllib.parse.urljoin(url, detail)
            if re.search(r"\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?.*)?$", detail, re.I):
                detail = ""  # 이미지 링크가 상세 URL로 잘못 추출된 경우
            out.append({
                "title": title, "start": s.isoformat() if s else None,
                "end": e.isoformat() if e else None, "deadline": dl.isoformat() if dl else None,
                "place": it.get("location") or "", "online": it.get("online") or "",
                "host": it.get("host") or name, "fee": it.get("fee") or "",
                "url": detail or url, "source": name, "group": group,
                "kind_hint": it.get("kind") or "", "desc": "",
            })
            kept += 1
        report[name] = f"{kept}건 (본문 불일치 제외 {dropped})" + (" · 무료 직접 읽기" if direct else "")
        print(f"  {name}: 추출 {len(items)} → 채택 {kept}, 본문 불일치 제외 {dropped}", file=log)
        if fp:
            hashes[name] = {"hash": fp, "full": today.isoformat()}
    json.dump(hashes, open(HASH_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


# ---------------------------------------------------------------- 후처리
def finalize(raw, today, days, log):
    until = today + timedelta(days=days)
    seen_path = os.path.join(DATA, "seen.json")
    seen = json.load(open(seen_path, encoding="utf-8")) if os.path.exists(seen_path) else {}

    merged = {}
    drops = []
    for ev in raw:
        s = parse_date(ev["start"])
        e = parse_date(ev["end"]) or s
        reason = None
        if not s:
            reason = "날짜없음"
        elif (e or s) < today:
            reason = "종료됨"
        elif s > until:
            reason = "기간밖"
        elif (e - s).days >= MAX_SPAN_DAYS:
            reason = "장기과정"
        elif NOISE.search(ev["title"]):
            reason = "잡음"
        # 학회·기관 공지 게시판의 "OO학술대회 오픈/등록/신청/접수 안내"류는 행사 자체가
        # 아니라 접수 시작을 알리는 게시물이며, 게시일이 개최일로 잘못 추출되기 쉽다.
        # 실제 개최일은 학회 공식 일정 페이지에서 별도로 수집하므로 이런 공지는 제외한다.
        elif ev["group"] in ("자동차기관", "학회") and re.search(
                r"학술대회.*(오픈|등록\s*안내|신청\s*안내|접수\s*안내|접수\s*시작)", ev["title"]):
            reason = "학술대회 등록안내(행사 아님)"
        tags = tag_event(ev["title"], ev.get("desc", "")) if not reason else []
        if not reason and not tags and ev["group"] == "전시장":
            tags = tag_expo(ev["title"])
        if not reason and not tags and ev["group"] in ("자동차기관", "학회"):
            tags = tag_expo(ev["title"])
            if not tags and ev["source"] in SOURCE_DEFAULT_TAG:
                tags = [SOURCE_DEFAULT_TAG[ev["source"]]]
        if not reason and not tags:
            reason = "키워드없음"
        if reason:
            drops.append({"reason": reason, "source": ev["source"], "title": ev["title"], "start": ev["start"]})
            continue
        k = norm_key(ev["title"], ev["start"])
        cur = merged.get(k)
        filled = sum(bool(ev.get(f)) for f in ("deadline", "place", "host", "fee"))
        if cur and cur["_filled"] >= filled:
            cur["sources"] = sorted(set(cur["sources"]) | {ev["source"]})
            continue
        online = ev.get("online") or ""
        kind = ("전시회" if ev["group"] == "전시장"
                and not re.search(r"회의|강연|교육|세미나|이벤트|공연", ev.get("kind_hint", ""))
                and not re.search(f"{CONF_PATTERN}|{ACAD_PATTERN}", ev["title"], re.I)
                else classify_kind(ev["title"], ev.get("kind_hint", ""), online))
        if (kind in ("교육", "세미나") and not set(tags) & AUTO_TAGS
                and EDU_EXCLUDE.search(f"{ev['title']} {ev.get('desc', '')}")):
            drops.append({"reason": "직무교육", "source": ev["source"], "title": ev["title"], "start": ev["start"]})
            continue
        ev2 = {
            "id": hashlib.md5(k.encode()).hexdigest()[:12],
            "title": ev["title"],
            # 전시장 일정은 원문 구분이 '회의·강연' 등이면 그 성격을 따르고, 아니면 전시회로 본다
            "kind": kind,
            "tags": tags,
            "start": ev["start"], "end": ev["end"] or ev["start"], "deadline": ev.get("deadline"),
            "place": ev.get("place", ""), "online": online, "host": ev.get("host", ""),
            "fee": ev.get("fee", ""), "url": ev["url"], "group": ev["group"],
            "sources": sorted(set((cur or {}).get("sources", [])) | {ev["source"]}),
            "_filled": filled,
        }
        merged[k] = ev2

    events = []
    for k, ev in merged.items():
        ev.pop("_filled")
        first = seen.setdefault(ev["id"], today.isoformat())
        ev["first_seen"] = first
        ev["is_new"] = first == today.isoformat()
        ev["notion_kind"] = KIND_TO_NOTION[ev["kind"]]
        events.append(ev)
    events.sort(key=lambda x: (x["start"], x["title"]))

    json.dump(seen, open(seen_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(drops, open(os.path.join(DATA, "dropped.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"정리 후 {len(events)}건 (원본 {len(raw)}건)", file=log)
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=122)
    ap.add_argument("--only", default="", help="쉼표로 구분한 firecrawl 소스명만 실행")
    ap.add_argument("--skip-firecrawl", action="store_true")
    ap.add_argument("--force-all", action="store_true",
                    help="바뀐 곳 감지를 끄고 모든 곳을 firecrawl로 새로 읽는다")
    ap.add_argument("--reprocess", action="store_true",
                    help="수집 없이 data/raw.json만 다시 정리 (규칙 수정 후 확인용, 크레딧 0)")
    args = ap.parse_args()

    os.makedirs(DATA, exist_ok=True)
    log = sys.stderr
    today = date.today()
    report = {}

    raw_path = os.path.join(DATA, "raw.json")
    cache = json.load(open(raw_path, encoding="utf-8")) if os.path.exists(raw_path) else {"raw": [], "report": {}}
    if args.reprocess:
        events = finalize(cache["raw"], today, args.days, log)
        report = cache["report"]
        raw = None
    else:
        raw = collect_all(args, today, log, report)
        # 이번에 수집하지 않은 firecrawl 소스(격주 건너뜀, --only 제외분)는 지난 결과를 유지
        fetched = {e["source"] for e in raw} | {k for k, v in report.items() if not v.startswith(("격주", "변경 없음"))}
        kept = [e for e in cache["raw"] if e["source"] not in fetched]
        for s in {e["source"] for e in kept}:
            report[s] = cache["report"].get(s, "").split(" (")[0] + " (지난 수집분)"
        raw += kept
        json.dump({"raw": raw, "report": report}, open(raw_path, "w", encoding="utf-8"), ensure_ascii=False)
        events = finalize(raw, today, args.days, log)
    write_output(events, report, args.days, log)


def collect_all(args, today, log, report):
    print("[이벤터스]", file=log)
    raw = from_eventus(args.days, log)
    report["이벤터스"] = f"{len(raw)}건"
    print("[온오프믹스]", file=log)
    oo = from_onoffmix(args.days, log)
    report["온오프믹스"] = f"{len(oo)}건"
    raw += oo
    if not args.skip_firecrawl:
        srcs = FIRECRAWL_SOURCES
        if args.only:
            names = set(args.only.split(","))
            srcs = [s for s in srcs if s[0] in names]
        elif today.isocalendar()[1] % 2:  # 홀수 주에는 격주 소스를 건너뜀
            skipped = [s[0] for s in srcs if s[3:] == ("biweekly",)]
            srcs = [s for s in srcs if s[3:] != ("biweekly",)]
            for n in skipped:
                report[n] = "격주 수집 (이번 주 건너뜀)"
        print(f"[firecrawl] {len(srcs)}곳", file=log)
        raw += from_firecrawl(srcs, today, log, report, force=args.force_all or bool(args.only))
    return raw


def write_output(events, report, days, log):
    payload = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "window_days": days,
        "sources": report,
        "source_groups": sorted({s[1] for s in FIRECRAWL_SOURCES} | {"행사플랫폼"}),
        "events": events,
    }
    with open(os.path.join(DATA, "events.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"저장: data/events.json ({len(events)}건, 신규 {sum(e['is_new'] for e in events)}건)", file=log)


if __name__ == "__main__":
    main()
