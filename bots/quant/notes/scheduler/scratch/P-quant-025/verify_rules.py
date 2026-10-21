import json, urllib.request
UA={"User-Agent":"Mozilla/5.0 (research)"}
def get(slug):
    u=f"https://gamma-api.polymarket.com/events?slug={slug}"
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40))[0]
def chicago(e):
    return [m for m in e["markets"] if m["slug"].endswith("chicago-il")][0]
quotes=[
 'This market will resolve to "Yes" if Chicago, IL falls within a tornado probability area rated ≥2% in the NOAA Storm Prediction Center Day 1 Convective Outlook on August 19, 2026.',
 'If the city\'s coordinates fall inside any area rated 2% or higher, that city resolves "Yes". If a city is outside all tornado probability areas, or only within areas rated below 2%, that city resolves "No".',
 'Borderline cases can be independently confirmed using the polygon data (excluding the hatched SIGN overlay, which is not a probability rating) and the city\'s listed coordinates.',
 'Resolution is based on the scheduled 01:00 UTC Day 1 Convective Outlook update issued on the following UTC calendar day. The SPC Day 1 outlook covers a 24-hour period from 12:00 UTC to 12:00 UTC the following day. Subsequent revisions published after that scheduled update will not be considered. If the SPC outlook is not published or is unavailable, the market remains open until data is available.',
 'This market uses coordinates 41.8781, -87.6298 for Chicago, IL.',
 'The resolution source for this market is the NOAA Storm Prediction Center at spc.noaa.gov.',
]
for slug,label in [("which-cities-face-tornado-risk-on-august-19-2026","aug19"),("which-cities-face-tornado-risk-on-september-30-2026","sep30")]:
    e=get(slug); m=chicago(e); desc=m.get("description","")
    print(f"== {label} {slug} ==")
    print("resolutionSource",m.get("resolutionSource"))
    print("feeSchedule",m.get("feeSchedule"))
    for q in quotes:
        print("QUOTE_PRESENT" if q in desc else "QUOTE_ABSENT", q[:70]+"...")
    old="If a city's coordinates fall inside any area rated 2% or higher"
    print("OLD_A_VARIANT_PRESENT" if old in desc else "OLD_A_VARIANT_ABSENT", old)
    if label=="sep30":
        for q in ['If the SPC Day 1 Convective Outlook has not been published by the time the market closes, this market will resolve to "No".',
                  'That scheduled update is the revisions cutoff; subsequent revisions published after it will not be considered.',
                  'The point-in-polygon test is performed on unprojected WGS84 (EPSG:4326) coordinates, which is the native coordinate system of the SPC GeoJSON data.']:
            print("SEP30_QUOTE_PRESENT" if q in desc else "SEP30_QUOTE_ABSENT", q[:90]+"...")
