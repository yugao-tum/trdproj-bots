"""Long-only cash ledger v1. No external funding, interest or execution guarantees."""
from datetime import date, timedelta
import math

class CapitalAccount:
    def __init__(self, fee=0.003, withdrawal_fee=0., delay_opens=0,
                 venue_cash=1250., external_cash=3750., sweep_target=1250., cap=2500.):
        if not (0 <= fee < 1 and withdrawal_fee >= 0 and delay_opens in (0,1)):
            raise ValueError('unsupported costs/delay')
        self.fee,self.withdrawal_fee,self.delay_opens=fee,withdrawal_fee,delay_opens
        self.cash,self.external=venue_cash,external_cash
        self.initial=venue_cash+external_cash
        self.target,self.cap=sweep_target,cap
        self.qty={};self.pending=[];self.fees=0.;self.withdrawal_costs=0.
        self.withdrawn=0.;self.trades=[];self.transfers=[];self.day=None
        self.open_pre=None;self.open_pre_conservative=None;self.day_gain=0.
        self.last_prices={};self.initialized=False
    def venue(self,prices):
        return self.cash+sum(q*self._price(prices,s) for s,q in self.qty.items() if q)
    @staticmethod
    def _price(prices,s):
        x=float(prices[s])
        if not math.isfinite(x) or x<=0: raise ValueError('invalid price')
        return x
    def transit(self): return sum(v for _,v in self.pending)
    def total(self,prices): return self.venue(prices)+self.external+self.transit()
    def begin_day(self,day,opens):
        day=str(day)[:10]
        if self.day is not None and day<=self.day: raise ValueError('days must increase')
        self.day=day
        self.day_gain=0.
        if self.initialized:
            self.day_gain=sum(q*(self._price(opens,s)-self.last_prices[s]) for s,q in self.qty.items() if q)
        self.initialized=True
        remaining=[]
        for due,value in self.pending:
            if due<=day:self.external+=value
            else:remaining.append((due,value))
        self.pending=remaining
        self.open_pre=self.venue(opens)
        self.open_pre_conservative=self.open_pre+self.transit()
        self.start_total=self.total(opens);self.start_fees=self.fees+self.withdrawal_costs
        self.last_prices={s:self._price(opens,s) for s,q in self.qty.items() if q}
        return {'open_pre':self.open_pre,'open_pre_conservative':self.open_pre_conservative,
                'open_pre_breach':self.open_pre>self.cap+1e-8}
    def _trade(self,s,delta,prices,reason):
        p=self._price(prices,s);n=abs(delta)*p;f=n*self.fee
        self.cash-=delta*p+f;self.qty[s]=self.qty.get(s,0.)+delta;self.fees+=f
        if self.cash < -1e-7 or self.qty[s] < -1e-9:raise AssertionError('unfunded trade')
        self.trades.append({'day':self.day,'symbol':s,'quantity_delta':delta,'price':p,'notional':n,'fee':f,'reason':reason})
    def rebalance(self,opens,target_notionals):
        """Targets USDT marked notional, sell first; proportional cash-constrained buys."""
        if any(not math.isfinite(v) or v<0 for v in target_notionals.values()):raise ValueError('long-only finite targets')
        symbols=sorted(set(self.qty)|set(target_notionals)); buys={}
        for s in symbols:
            p=self._price(opens,s);delta=target_notionals.get(s,0.)/p-self.qty.get(s,0.)
            if delta < -1e-12:self._trade(s,delta,opens,'rebalance')
            elif delta>1e-12:buys[s]=delta
        need=sum(d*self._price(opens,s)*(1+self.fee) for s,d in buys.items())
        scale=min(1.,max(self.cash,0.)/need) if need else 1.
        for s,d in buys.items():
            if scale:self._trade(s,d*scale,opens,'rebalance')
        self.last_prices={s:self._price(opens,s) for s,q in self.qty.items() if q}
        return scale
    def sweep(self,opens):
        """Withdraw equity above target, never replenish; fee deducted from gross transfer."""
        excess=self.venue(opens)-self.target
        if excess<=1e-9:return 0.
        gross_sale=max(0.,excess-self.cash)
        gross_transfer=excess-gross_sale*self.fee
        if gross_transfer<=self.withdrawal_fee+1e-9:return 0.
        mv=sum(q*self._price(opens,s) for s,q in self.qty.items() if q)
        if gross_sale:
            for s,q in list(self.qty.items()):
                if q:self._trade(s,-q*gross_sale/mv,opens,'sweep')
        self.cash-=gross_transfer
        net=gross_transfer-self.withdrawal_fee
        self.withdrawal_costs+=self.withdrawal_fee;self.withdrawn+=net
        due=(date.fromisoformat(self.day)+timedelta(days=self.delay_opens)).isoformat()
        if self.delay_opens:self.pending.append((due,net))
        else:self.external+=net
        self.transfers.append({'day':self.day,'due':due,'gross':gross_transfer,'fee':self.withdrawal_fee,'net':net})
        if self.cash < -1e-7:raise AssertionError('negative sweep cash')
        self.last_prices={s:self._price(opens,s) for s,q in self.qty.items() if q}
        return net
    def snapshot(self,closes,highs=None):
        mv=sum(q*self._price(closes,s) for s,q in self.qty.items() if q)
        venue=self.cash+mv;total=venue+self.external+self.transit()
        intraday=sum(q*(self._price(closes,s)-self.last_prices[s]) for s,q in self.qty.items() if q)
        costs=self.fees+self.withdrawal_costs-self.start_fees
        residual=total-self.start_total-intraday+costs
        if abs(residual)>1e-7:raise AssertionError('conservation failure: '+str(residual))
        high=self.cash+sum(q*self._price(highs,s) for s,q in self.qty.items() if q) if highs is not None else None
        result={'day':self.day,'venue_cash':self.cash,'position_value':mv,'external_cash':self.external,
                'in_transit':self.transit(),'total_equity':total,'net_pnl':total-self.initial,
                'net_liquidation_equity':total-mv*self.fee,'trade_fees':self.fees,
                'withdrawal_fees':self.withdrawal_costs,'net_withdrawn':self.withdrawn,
                'open_pre':self.open_pre,'open_pre_conservative':self.open_pre_conservative,
                'close_venue':venue,'high_upper_venue':high,
                'open_breach':self.open_pre>self.cap+1e-8,'close_breach':venue>self.cap+1e-8,
                'high_upper_exceeds':high>self.cap+1e-8 if high is not None else None,
                'conservation_residual':residual,'daily_pnl':self.day_gain+intraday-costs}
        self.last_prices={s:self._price(closes,s) for s,q in self.qty.items() if q}
        return result
    def liquidate_after_snapshot(self,closes):
        """Terminal close fill assumption, call AFTER final snapshot; no second snapshot."""
        before=self.total(closes);fees_before=self.fees
        self.rebalance(closes,{})
        after=self.total(closes);cost=self.fees-fees_before
        residual=after-before+cost
        if abs(residual)>1e-7:raise AssertionError('terminal conservation failure')
        return {'terminal_equity':after,'terminal_pnl':after-self.initial,
                'terminal_sale_fee':cost,'terminal_residual':residual,
                'venue_cash':self.cash,'external_cash':self.external,'in_transit':self.transit()}
