"""data/events.json -> out/dashboard/index.html (데이터를 페이지에 내장)."""
import json
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REGIONS = ["서울", "경기", "인천", "부산", "대구", "대전", "광주", "울산", "세종", "강원",
           "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
ALIASES = {
    "코엑스": "서울", "COEX": "서울", "섬유센터": "서울", "양재": "서울", "여의도": "서울",
    "킨텍스": "경기", "KINTEX": "경기", "고양": "경기", "성남": "경기", "판교": "경기", "수원": "경기",
    "벡스코": "부산", "BEXCO": "부산", "해운대": "부산", "엑스코": "대구", "EXCO": "대구",
    "여수": "전남", "천안": "충남", "청주": "충북", "오창": "충북", "창원": "경남", "송도": "인천",
    "충청남도": "충남", "충청북도": "충북", "전라남도": "전남", "전라북도": "전북", "전북특별자치도": "전북",
    "경상남도": "경남", "경상북도": "경북", "강원특별자치도": "강원", "제주특별자치도": "제주",
    "전남광주": "광주",
}


def region_of(ev):
    text = f"{ev.get('place', '')} {ev.get('host', '')} {ev.get('title', '')}"
    if ev.get("online") == "온라인" or re.match(r"\s*온라인", ev.get("place", "")):
        return "온라인"
    for k, v in ALIASES.items():
        if k in text:
            return v
    for r in REGIONS:
        if r in text:
            return r
    return "기타"


def main():
    payload = json.load(open(os.path.join(HERE, "data", "events.json"), encoding="utf-8"))
    for ev in payload["events"]:
        ev["region"] = region_of(ev)
    tpl = open(os.path.join(HERE, "out", "dashboard", "template.html"), encoding="utf-8").read()
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    out = tpl.replace("/*__DATA__*/", data)
    path = os.path.join(HERE, "out", "dashboard", "index.html")
    open(path, "w", encoding="utf-8").write(out)
    print(f"{path} ({len(payload['events'])}건, {len(out) // 1024}KB)")


if __name__ == "__main__":
    main()
