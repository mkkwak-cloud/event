"""firecrawl 없이 받은 화면(HTML)에서 행사 목록을 직접 뽑는 읽기 코드 (크레딧 0).

각 함수는 (html, 목록주소) -> firecrawl 추출 결과와 같은 모양의 dict 목록을 돌려준다.
(title, start_date, end_date, location, detail_url, kind, host, fee ...)
0건이 나오면 collect.py가 firecrawl로 되돌아가므로, 화면 모양이 바뀌어도 수집은 끊기지 않는다.
"""
import html as htmllib
import re
import urllib.parse


def _t(s):
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()


def _dates(s):
    return re.findall(r"20\d{2}[-./]\s*\d{1,2}[-./]\s*\d{1,2}", s)


def _item(title, dates, place="", url="", kind="", host=""):
    return {"title": title, "start_date": dates[0] if dates else "",
            "end_date": dates[-1] if dates else "", "registration_deadline": "",
            "location": place, "online": "", "host": host, "fee": "",
            "detail_url": url, "kind": kind}


def etnews(h, base):
    out = []
    for li in re.findall(r"(?s)<li>(.*?)</li>", h):
        m = re.search(r'<span class="date">(.*?)</span>.*?<strong><a href="([^"]+)"[^>]*>(.*?)</a>', li, re.S)
        if not m:
            continue
        cat = re.search(r'<span class="category">(.*?)</span>', li, re.S)
        out.append(_item(_t(m.group(3)), _dates(m.group(1)), "", urllib.parse.urljoin(base, m.group(2)),
                         _t(cat.group(1)) if cat else ""))
    return out


def kiot(h, base):
    out = []
    for tr in re.findall(r"(?s)<tr onclick=\"window\.location\.href='([^']+)'\"[^>]*>(.*?)</tr>", h):
        href, body = tr
        tds = re.findall(r"(?s)<td[^>]*>(.*?)</td>", body)
        if len(tds) < 4:
            continue
        out.append(_item(_t(tds[1]), _dates(_t(tds[2])), _t(tds[3]),
                         urllib.parse.urljoin(base, htmllib.unescape(href))))
    return out


def ksme(h, base):
    out = []
    for tr in re.findall(r'(?s)<tr bgcolor="#FFFFFF" class="basic">(.*?)</tr>', h):
        a = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', tr, re.S)
        d = re.search(r'<div class="style3">(.*?)</div>', tr, re.S)
        if not (a and d):
            continue
        tds = re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)
        place = _t(re.sub(r"(?s)<!--.*?-->", "", tds[2])) if len(tds) > 2 else ""
        out.append(_item(_t(a.group(2)), _dates(d.group(1)), place,
                         urllib.parse.urljoin(base, htmllib.unescape(a.group(1)))))
    return out


def ksae_schedule(h, base):
    out = []
    for tr in re.findall(r"(?s)<tr id=\"\d+\">(.*?)</tr>", h):
        tds = re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)
        if len(tds) < 3 or not _t(tds[0]):
            continue
        a = re.search(r'<a href="([^"]+)"', tds[0])  # 링크 없는 행도 있다(닫는 태그만 있음)
        out.append(_item(_t(tds[0]), _dates(_t(tds[1])), _t(tds[2]),
                         urllib.parse.urljoin(base, a.group(1)) if a else base))
    return out


def korcham(h, base):
    out = []
    for tr in re.findall(r"(?s)<tr>(.*?)</tr>", h):
        a = re.search(r'<td class="tl"><a href="([^"]+)"[^>]*>(.*?)</a>', tr, re.S)
        d = re.search(r'<p class="date">(.*?)</p>', tr, re.S)
        if not (a and d):
            continue
        link = re.search(r"'(https?://[^']+)'", a.group(1))
        out.append(_item(_t(a.group(2)), _dates(_t(d.group(1))), "",
                         link.group(1) if link else base, host="대한상공회의소"))
    return out


DIRECT_PARSERS = {
    "전자신문": etnews,
    "KIoT": kiot,
    "대한기계학회": ksme,
    "KSAE 연간일정": ksae_schedule,
    "대한상공회의소": korcham,
}
