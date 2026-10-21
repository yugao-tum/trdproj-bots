import os,re,glob,csv,datetime as dt,html
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
def clean(s): return html.unescape(re.sub(r'<[^>]+>',' ',s)).replace('\xa0',' ')
rows=[]
for p in sorted(glob.glob(os.path.join(CACHE,'aaa_2026*.html'))):
    t=os.path.basename(p)[4:18]
    h=open(p,encoding='utf-8',errors='replace').read()
    m_asof=re.search(r'Price as of\s*(?:<br\s*/?>)?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2})',h)
    m_today=re.search(r"Today[’']s AAA National Average\s*\$?([0-9]+\.[0-9]{4})",h)
    # table rows
    cur=re.search(r'<td>\s*Current Avg\.\s*</td>\s*<td>\s*\$?([0-9]+\.[0-9]{4})',h)
    yest=re.search(r'<td>\s*Yesterday Avg\.\s*</td>\s*<td>\s*\$?([0-9]+\.[0-9]{4})',h)
    if not (m_asof and cur and yest):
        print('PARSE_FAIL',t,bool(m_asof),bool(cur),bool(yest)); continue
    rows.append(dict(snapshot_utc=t,price_as_of=m_asof.group(1),today=(m_today.group(1) if m_today else ''),
                     current_regular=cur.group(1),yesterday_regular=yest.group(1),bytes=os.path.getsize(p)))
rows.sort(key=lambda r:r['snapshot_utc'])
with open(os.path.join(BASE,'aaa_snapshots_all.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['snapshot_utc','price_as_of','today','current_regular','yesterday_regular','bytes'])
    w.writeheader(); w.writerows(rows)
print('parsed',len(rows))
for r in rows: print(r)
