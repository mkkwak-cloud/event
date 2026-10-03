"""firecrawl 없이 무료로 읽을 수 있는 곳 시험 (크레딧 0, 읽기 전용).

각 수집처 주소를 직접 받아서
 - 받아졌는지(상태·크기)
 - 지난번 수집된 행사 제목이 받은 화면에 보이는지(직접 읽기 가능 여부)
 - 5초 뒤 다시 받았을 때 같은지(바뀐 곳 감지 가능 여부)
를 data/free_probe.json 에 저장한다.
"""
import json
import os
import re
import ssl
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect  # noqa: E402

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def fetch(url):
    req = urllib.request.Request(url, headers=collect.UA)
    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
            b = r.read()
            m = re.search(rb'charset=["\']?([\w-]+)', b[:4000])
            enc = m.group(1).decode() if m else (r.headers.get_content_charset() or "utf-8")
            try:
                return r.status, b.decode(enc, "replace")
            except LookupError:
                return r.status, b.decode("utf-8", "replace")
    except Exception as ex:
        return str(ex)[:60], ""


def norm(s):
    return re.sub(r"\s+", "", s)


def stable_text(h):
    h = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", "", h)
    h = re.sub(r"(?s)<!--.*?-->", "", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return norm(h)


def main():
    cache = json.load(open(os.path.join(collect.DATA, "raw.json"), encoding="utf-8"))
    titles = {}
    for e in cache["raw"]:
        titles.setdefault(e["source"], []).append(e["title"])
    res = {}
    for name, group, url, *_ in collect.FIRECRAWL_SOURCES:
        st, h1 = fetch(url)
        time.sleep(5)
        st2, h2 = fetch(url)
        ts = titles.get(name, [])
        n1 = norm(h1)
        hit = sum(1 for t in ts if norm(t)[:10] and norm(t)[:10] in n1)
        same = bool(h1) and stable_text(h1) == stable_text(h2)
        res[name] = {"url": url, "status": st, "bytes": len(h1), "cached_titles": len(ts),
                     "titles_visible": hit, "same_after_5s": same}
        print(f"{name:14} 상태={st} 크기={len(h1):>8} 제목보임={hit}/{len(ts)} 5초뒤동일={same}")
    json.dump(res, open(os.path.join(collect.DATA, "free_probe.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
