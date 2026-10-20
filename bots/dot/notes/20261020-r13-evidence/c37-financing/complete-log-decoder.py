#!/usr/bin/env python3
"""Offline receipt decoder. No network, secrets, traces or balance assumptions."""
import json,re,hashlib,csv,collections,pathlib
O=pathlib.Path(__file__).resolve().parent
MASK=(1<<64)-1
RC=[0x1,0x8082,0x800000000000808a,0x8000000080008000,0x808b,0x80000001,0x8000000080008081,0x8000000000008009,0x8a,0x88,0x80008009,0x8000000a,0x8000808b,0x800000000000008b,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x800a,0x800000008000000a,0x8000000080008081,0x8000000000008080,0x80000001,0x8000000080008008]
ROT=[[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
def rol(x,n):return ((x<<n)|(x>>(64-n)))&MASK if n else x
def keccak(data):
 p=bytearray(data);p.append(1)
 while len(p)%136!=135:p.append(0)
 p.append(128);a=[0]*25
 for off in range(0,len(p),136):
  for i in range(17):a[i]^=int.from_bytes(p[off+8*i:off+8*i+8],'little')
  for rc in RC:
   c=[a[x]^a[x+5]^a[x+10]^a[x+15]^a[x+20] for x in range(5)];d=[c[(x-1)%5]^rol(c[(x+1)%5],1) for x in range(5)]
   for i in range(25):a[i]^=d[i%5]
   b=[0]*25
   for x in range(5):
    for y in range(5):b[y+5*((2*x+3*y)%5)]=rol(a[x+5*y],ROT[x][y])
   for x in range(5):
    for y in range(5):a[x+5*y]=b[x+5*y]^((~b[(x+1)%5+5*y])&b[(x+2)%5+5*y])
   a[0]^=rc
 return b''.join(x.to_bytes(8,'little') for x in a)[:32].hex()
def schemas():
 out={};bindings=[]
 for f in sorted((O/'sources').glob('*.json')):
  if f.name=='vault.json':continue
  s=json.loads(f.read_text())['structuredContent'];body=s.get('content','')
  if not body:continue
  bindings.append({'file':f.name,'url':s.get('display_url'),'git_blob_sha':s.get('sha'),'content_sha256':hashlib.sha256(body.encode()).hexdigest()})
  for name,args in re.findall(r'event\s+(\w+)\s*\((.*?)\)\s*;',body,re.S):
   fields=[]
   for arg in args.split(','):
    t=arg.strip().split();typ=t[0].replace('DataTypes.InterestRateMode','uint8').replace('PoolSpecialization','uint8')
    if typ.startswith('I'):typ='address'+('[]' if typ.endswith('[]') else '')
    fields.append((typ,t[-1],'indexed' in t))
   sig=name+'('+','.join(x[0] for x in fields)+')';topic='0x'+keccak(sig.encode());out[topic]={'name':name,'signature':sig,'fields':fields,'source_file':f.name}
 return out,bindings
def value(t,w):
 n=int(w,16)
 if t=='address':
  assert n<2**160
  return '0x'+w[-40:]
 if t=='bool':assert n in [0,1];return bool(n)
 if t.startswith('bytes'):return '0x'+w
 if t.startswith('int') and n>=2**255:n-=2**256
 if t.startswith('uint'):assert n<2**int(t[4:])
 return str(n)
def decode(log,sc):
 e={'log_index':int(log['logIndex'],16),'emitter':log['address'],'topic0':log['topics'][0] if log['topics'] else None,'raw_topics':log['topics'],'raw_data':log['data'],'status':'unknown_signature'}
 s=sc.get(e['topic0'])
 if not s:return e
 e.update(event=s['name'],signature=s['signature'],source_file=s['source_file']);data=log['data'][2:];words=[data[i:i+64] for i in range(0,len(data),64)]
 try:
  assert len(data)%64==0;assert len(log['topics'])==1+sum(x[2] for x in s['fields']);ti=1;di=0;vals={}
  for typ,name,idx in s['fields']:
   if idx:w=log['topics'][ti][2:];ti+=1
   else:w=words[di];di+=1
   if typ.endswith('[]'):
    assert not idx;start=int(w,16)//32;assert int(w,16)%32==0;n=int(words[start],16);assert start+n<len(words);vals[name]=[value(typ[:-2],z) for z in words[start+1:start+1+n]]
   else:vals[name]=value(typ,w)
  if not any(x[0].endswith('[]') for x in s['fields']):assert len(words)==di
  e.update(status='decoded',fields=vals)
 except (AssertionError,IndexError,ValueError) as exc:e.update(status='schema_mismatch',error=type(exc).__name__)
 return e
def classify(loans,payers,vault):
 return [e for e in loans if e['emitter']==vault and e.get('signature')=='FlashLoan(address,address,uint256,uint256)' and e['fields'].get('recipient') in payers]
def main():
 manifest=json.loads((O.parent/'input-manifest.json').read_text());verification=[]
 for x in manifest['inputs']:
  p=pathlib.Path(x['path']);actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==x['sha256'];verification.append({'path':str(p),'sha256':actual,'verified':True})
 sc,bindings=schemas();vault=json.loads(json.loads((O/'sources/balancer-address.json').read_text())['structuredContent']['content'])['Vault'].lower();assert keccak(b'')=='c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470';assert '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' in sc
 receipts=[]
 for x in manifest['inputs']:
  p=pathlib.Path(x['path'])
  if p.name=='independent-receipts.json':receipts+=json.loads(p.read_text())
  elif re.match('temporal-stratum-\\d+-receipt.json',p.name):receipts.append(json.loads(p.read_text()))
 assert len(receipts)==12
 alltx=[];rows=[]
 for wrapper in receipts:
  r=wrapper['result'];events=[decode(l,sc) for l in sorted(r['logs'],key=lambda z:int(z['logIndex'],16))];assert len(events)==len(r['logs']);assert len({e['log_index'] for e in events})==len(events)
  liq=[e for e in events if e.get('event')=='LiquidationCall' and e['status']=='decoded'];payers={e['fields']['liquidator'] for e in liq};loans=[e for e in events if e.get('event') in ['FlashLoan','Borrow'] and e['status']=='decoded'];flows=[e for e in events if e.get('event')=='Transfer' and e['status']=='decoded' and ({e['fields']['from'],e['fields']['to']}&payers)]
  linked=classify(loans,payers,vault);classification='borrowed_event_linked_to_liquidator' if linked else 'unknown'
  row={'transaction_hash':r['transactionHash'],'log_count':len(events),'decoded_count':sum(e['status']=='decoded' for e in events),'unknown_count':sum(e['status']=='unknown_signature' for e in events),'mismatch_count':sum(e['status']=='schema_mismatch' for e in events),'liquidations':len(liq),'loan_events':len(loans),'linked_loan_events':len(linked),'classification':classification,'own_funds_proven':False};rows.append(row)
  summaries=[]
  for payer in sorted(payers):
   token_sums={}
   for e in flows:
    a=token_sums.setdefault(e['emitter'],{'in':0,'out':0});v=int(e['fields']['value'])
    if e['fields']['to']==payer:a['in']+=v
    if e['fields']['from']==payer:a['out']+=v
   summaries.append({'address':payer,'token_units':{t:{'in':str(v['in']),'out':str(v['out']),'net_event_flow':str(v['in']-v['out'])} for t,v in token_sums.items()}})
  evidence=[]
  transfers=[e for e in events if e.get('event')=='Transfer' and e['status']=='decoded']
  for loan in linked:
   f=loan['fields'];token=f['token'];recipient=f['recipient'];amount=int(f['amount']);fee=int(f['feeAmount'])
   outgoing=[e for e in transfers if e['emitter']==token and e['fields']['from']==vault and e['fields']['to']==recipient and int(e['fields']['value'])==amount]
   returned=[e for e in transfers if e['emitter']==token and e['fields']['to']==vault and int(e['fields']['value'])>=amount+fee]
   evidence.append({'loan_log':loan['log_index'],'verified_emitter':vault,'disbursement_logs':[e['log_index'] for e in outgoing],'repayment_to_vault_logs':[e['log_index'] for e in returned],'repayment_senders':[e['fields']['from'] for e in returned],'note':'Repayment may be routed directly from a swap pool; event-flow is not trace-level causality.'})
  alltx.append(dict(row,token_flow_totals=summaries,financing_evidence=evidence,events=events,liquidation_payment_addresses=sorted(payers),liquidator_token_flows=flows,loan_events_detail=loans,limitation='Event provenance and transfer flow, not traces/prestate or exclusive fungible-capital allocation; no PnL.'))
 (O/'decoded-events.json').write_text(json.dumps(alltx,indent=2)+'\n');(O/'abi-source-bindings.json').write_text(json.dumps({'sources':bindings,'schemas':sc,'input_verification':verification},indent=2)+'\n')
 with (O/'financing-classification.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps(rows,indent=2));print('PASS: Keccak empty vector, ERC20 known topic, all input hashes, 12 receipts, unique ordered log indexes and no dropped logs')
if __name__=='__main__':main()
