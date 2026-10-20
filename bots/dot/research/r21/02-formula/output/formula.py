"""Offline symbolic/Decimal isolated linear-short diagnostics, not venue certification."""
from decimal import Decimal, localcontext

def D(x):
    return x if isinstance(x, Decimal) else Decimal(str(x))

def isolated_short_equity(wallet, quantity, entry_price, mark_price):
    w,q,e,p=map(D,(wallet,quantity,entry_price,mark_price))
    if q <= 0 or e <= 0 or p <= 0:
        raise ValueError('Positive quantity and prices required')
    return w + q*(e-p)

def maintenance_margin(quantity, mark_price, rate, deduction):
    if deduction is None:
        raise ValueError('Unknown deduction cannot silently become zero')
    q,p,r,d=map(D,(quantity,mark_price,rate,deduction))
    if q <= 0 or p <= 0 or r < 0:
        raise ValueError('Invalid inputs')
    return q*p*r-d

def short_equality_price(wallet, quantity, entry_price, rate, deduction, assumed_close_cost=0):
    """Own algebra from equity=MM+optional close reserve, within one applicable tier.
    Optional cost is a research reserve, not asserted exchange liquidation formula.
    """
    if deduction is None:
        raise ValueError('Specify deduction assumption/evidence explicitly')
    w,q,e,r,d,c=map(D,(wallet,quantity,entry_price,rate,deduction,assumed_close_cost))
    if q<=0 or e<=0 or r<0 or c<0:
        raise ValueError('Invalid inputs')
    with localcontext() as ctx:
        ctx.prec=60
        return (w+q*e+d)/(q*(1+r+c))

def in_tier(quantity, mark_price, floor, cap):
    q,p,lo,hi=map(D,(quantity,mark_price,floor,cap))
    return lo < q*p <= hi

def margin_buffer(wallet, quantity, entry_price, mark_price, rate, deduction, assumed_close_cost=0):
    q,p,c=map(D,(quantity,mark_price,assumed_close_cost))
    return isolated_short_equity(wallet,q,entry_price,p)-maintenance_margin(q,p,rate,deduction)-q*p*c
