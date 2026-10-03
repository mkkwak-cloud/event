import re, sys, urllib.request, urllib.parse, ssl, html
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
KW = re.compile(r'행사|세미나|컨퍼런스|포럼|전시|교육|설명회|공지|알림|이벤트|event|conference|seminar', re.I)
def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0'}), timeout=20, context=ctx)
    b = r.read(); enc = 'utf-8'
    m = re.search(rb'charset=["\']?([\w-]+)', b[:3000])
    if m: enc = m.group(1).decode()
    return r.geturl(), b.decode(enc, 'replace')
for u in sys.argv[1:]:
    try:
        final, h = get(u)
    except Exception as e:
        print('##', u, 'ERR', e); continue
    seen = set(); out = []
    for href, txt in re.findall(r'<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', h, re.S|re.I):
        t = html.unescape(re.sub(r'<[^>]+>|\s+', ' ', txt)).strip()
        if not t or len(t) > 40 or not KW.search(t + ' ' + href): continue
        full = urllib.parse.urljoin(final, href)
        if full in seen or 'javascript' in full: continue
        seen.add(full); out.append(f'   {t[:30]:<30} {full}')
    print('##', u, '->', final, f'({len(h)}b)'); print('\n'.join(out[:18]))
