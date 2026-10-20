import json, urllib.request, re, sys
ENTRY='../../../../entries/quant-026-drought-d4-weekly-continuity.md'
text=open(ENTRY,encoding='utf-8').read()
def block(start_marker,end_marker):
    a=text.index(start_marker); a=text.index('\n',a)+1
    b=text.index(end_marker,a)
    seg=text[a:b]
    paras=[]
    for line in seg.splitlines():
        if line.startswith('> '): paras.append(line[2:])
        elif line.strip()=='>': paras.append('')
    # collapse quote blank separators into paragraph breaks
    return '\n'.join(paras).strip()
def get(slug):
    url='https://gamma-api.polymarket.com/events?slug='+slug
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    ev=json.loads(urllib.request.urlopen(req,timeout=60).read())[0]
    mk=ev['markets'][0]
    return ev,mk
checks=[('state-d4-drought-2026-10-13','规则原文（州市场','模板二（州数）'),
        ('states-in-d4-drought-2026-10-13','模板二（州数）','几个要点')]
ok=True
for slug,a,b in checks:
    q=block(a,b)
    ev,mk=get(slug)
    live=mk['description'].strip()
    same=(q==live)
    print(f'{slug}: quoted {len(q)} chars, live market description {len(live)} chars, exact_match={same}')
    if not same:
        ok=False
        import difflib
        for d in list(difflib.unified_diff(live.splitlines(),q.splitlines(),'live','entry',lineterm=''))[:40]: print(d)
    print('  event resolutionSource=',repr(ev.get('resolutionSource')),'market resolutionSource=',repr(mk.get('resolutionSource')))
print('ALL_QUOTES_VERBATIM',ok)
sys.exit(0 if ok else 1)
