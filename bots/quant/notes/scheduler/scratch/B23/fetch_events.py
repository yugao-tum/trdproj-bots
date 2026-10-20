import json, urllib.request, os
url = 'https://gamma-api.polymarket.com/events?series_id=12688&closed=true&limit=100'
os.makedirs('_cache', exist_ok=True)
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urllib.request.urlopen(req, timeout=90).read())
json.dump(data, open('_cache/events_closed0.json', 'w'))
print('events', len(data), 'bytes', os.path.getsize('_cache/events_closed0.json'))
print('markets', sum(len(e.get('markets') or []) for e in data))
