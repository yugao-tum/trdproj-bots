import urllib.request, urllib.parse, time, os, json, sys
FIPS = {
 'AL':'01','AZ':'04','AR':'05','CA':'06','CO':'08','CT':'09','DE':'10','FL':'12','GA':'13','ID':'16',
 'IL':'17','IN':'18','IA':'19','KS':'20','KY':'21','LA':'22','ME':'23','MD':'24','MA':'25','MI':'26',
 'MN':'27','MS':'28','MO':'29','MT':'30','NE':'31','NV':'32','NH':'33','NJ':'34','NM':'35','NY':'36',
 'NC':'37','ND':'38','OH':'39','OK':'40','OR':'41','PA':'42','RI':'44','SC':'45','SD':'46','TN':'47',
 'TX':'48','UT':'49','VT':'50','VA':'51','WA':'53','WV':'54','WI':'55','WY':'56'}
os.makedirs('_cache/usdm', exist_ok=True)
base='https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent'
for st,fips in FIPS.items():
    p=f'_cache/usdm/{st}.csv'
    if os.path.exists(p) and os.path.getsize(p)>1000: continue
    q=urllib.parse.urlencode({'aoi':fips,'startdate':'1/1/2000','enddate':'10/20/2026','statisticsType':'1'})
    req=urllib.request.Request(base+'?'+q, headers={'User-Agent':'Mozilla/5.0','Accept':'text/csv'})
    try:
        data=urllib.request.urlopen(req, timeout=90).read()
        open(p,'wb').write(data)
        print(st, len(data), flush=True)
    except Exception as e:
        print('ERR',st,e, flush=True)
    time.sleep(0.2)
