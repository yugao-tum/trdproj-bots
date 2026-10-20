#!/usr/bin/env python3
"""Validate published aggregate consistency only, not re-decode raw receipts."""
import csv,pathlib,collections
P=pathlib.Path(__file__).resolve().parent
rows=list(csv.DictReader((P/'financing-classification.csv').open()))
assert len(rows)==12
assert sum(int(r['log_count']) for r in rows)==1295
assert sum(int(r['decoded_count']) for r in rows)==1229
assert sum(int(r['unknown_count']) for r in rows)==66
assert sum(int(r['mismatch_count']) for r in rows)==0
assert sum(int(r['liquidations']) for r in rows)==80
assert all(r['own_funds_proven']=='False' for r in rows)
assert collections.Counter(r['classification'] for r in rows)=={'unknown':9,'borrowed_event_linked_to_liquidator':3}
chain=list(csv.DictReader((P/'borrowed-evidence-chain.csv').open()))
assert len(chain)==3
assert {r['transaction_hash'] for r in chain}=={r['transaction_hash'] for r in rows if r['classification']!='unknown'}
assert all(r['verified_vault']=='0xba12222222228d8ba445958a75a0704d566bf2c8' and r['disbursement_logs'] and r['repayment_logs'] for r in chain)
print('PASS: aggregate consistency only; 3 borrowed /9 unknown /0 self-funded proved; not a raw-receipt replay or PnL test')
