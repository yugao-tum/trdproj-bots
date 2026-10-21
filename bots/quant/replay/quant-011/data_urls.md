# quant-011 data URLs (all keyless, free, accessed 2026-10-21)

## Polymarket closed events (Gamma keyset)
- `https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=EPL&limit=100`
- `https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=premier-league&limit=100`
- `https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=serie-a&limit=100`
- `https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=la-liga&limit=100`
- `https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=bundesliga&limit=100`
- `https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=ligue-1&limit=100`
- Pagination: add `&after_cursor=<next_cursor>` from the previous response.

## Polymarket per-trade fills (data-api)
- `https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=0`
- The script pages `offset` by 500 until the oldest print is before the 24h window.
- Fields used: `conditionId`, `outcome`, `price`, `size`, `side`, `timestamp`.
- Public limit: roughly the latest 20,000 prints per market.

## Football-data.co.uk (base rates and results)
- Template: `https://www.football-data.co.uk/mmz4281/<season>/<league>.csv`
- seasons: `1718 1819 1920 2021 2122 2223 2324 2425 2526 2627`
- leagues: `E0 I1 SP1 D1 F1`
- Example: `https://www.football-data.co.uk/mmz4281/2425/E0.csv`
- `2021` is the 2020/21 season code; `2122` is 2021/22.

## Fees
- `https://docs.polymarket.com/trading/fees`
- `fee = C × feeRate × p × (1 - p)`; "Makers are never charged fees. Only takers pay fees."; Sports 0.05 / maker 0 / rebate 15%.

## Not used as a fill price
- `https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60`
- This is last-trade / midpoint history, not a fill price (GUIDE §2.1). The replay never uses it.
