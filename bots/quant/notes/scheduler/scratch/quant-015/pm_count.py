import json, re
d = json.load(open('_cache/search.json'))
ev = d['events']
pref = ['january','february','march','april','may','june','july','august','september','october','november','december']
def monthkey(e):
    s = e['slug'].lower()
    m = re.match(r'(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{4})', s)
    if m:
        return (int(m.group(2)), pref.index(m.group(1))+1)
    if 'april-2024' in s:
        return (2024, 4)
    return None
keys = {}
for e in ev:
    keys.setdefault(monthkey(e), []).append(e['slug'])
print('search events:', len(ev), 'closed:', sum(bool(e.get('closed')) for e in ev), 'open:', sum(not e.get('closed') for e in ev))
print('distinct calendar months:', len([k for k in keys if k]))
for k in sorted(keys, key=lambda x: (x is None, x or (0, 0))):
    print(k, keys[k])
