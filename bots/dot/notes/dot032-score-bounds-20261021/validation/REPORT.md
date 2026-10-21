# Independent validation: dot032 score-grouping bounds

Verdict: PASS for the stated continuous score-mass relaxation, with mandatory scope restrictions. Not a market implementation, cash-reward estimate, strategy, or profitability result. No market data, model calls, external writes, or old crypto results were used. Existing SciPy was used without installation.

## Source and rule check

Checked the cached official page https://docs.polymarket.com/programs/liquidity-rewards (cached source SHA-256 recorded in ../SOURCES.json), especially source lines 174–187, 201–243. The cache says c=3. The max/min formula applies INSIDE the inclusive adjusted-midpoint interval [0.10,0.90]. Outside that interval the formula is min(a,b). Market eligibility precedes scoring; qualifying size/spread and the adjusted midpoint must be established. The two score legs combine complementary books, not merely bid and ask of one token. Normalization includes the maker's own score. Epoch normalization follows sample normalization; daily payout has a minimum threshold. No independent current-live configuration verification was attempted or needed for this conditional mathematical audit.

## Independent proof

Let nonnegative per-maker eligible score masses be (a_i,b_i), A=sum a_i, B=sum b_i, and f(a,b)=max(min(a,b),max(a,b)/3). Define L=max(A/3,B/3,(A+B)/4), U=min(A,B)+abs(A-B)/3.

For each maker, f>=a/3, f>=b/3. Writing x=max(a,b), y=min(a,b), if x>=3y then f=x/3>=(x+y)/4; otherwise f=y>=(x+y)/4. Summing proves sum f>=L.

Also f<=(a+b+min(a,b))/3: in x>=3y this is immediate; otherwise y<=(x+2y)/3 because y<=x. Thus sum f<=(A+B+sum min(a_i,b_i))/3<=(A+B+min(A,B))/3=U.

Lower endpoint witnesses: if A>=3B or B>=3A, one maker holding (A,B) attains L. Otherwise put x=(3A-B)/8, y=(3B-A)/8 and use maker masses (3x,x),(y,3y). Nonnegative x,y exist and the total score is x+y=(A+B)/4. Upper endpoint: use (m,m) and (A-m,B-m), m=min(A,B). Zero mass groups can be omitted. At most two nonzero makers suffice in this relaxation. A fixed single maker can fail to attain either proposed extremum; maker-count assumptions matter.

Outside midrange, g(a,b)=min(a,b). The corresponding unrestricted relaxed bounds are 0<=sum g<=min(A,B), attained by separating both legs or combining them. The midrange lower bound MUST NOT be applied there.

## Realizability restrictions and counterexample

The theorem permits continuously divisible score masses and arbitrary assignment to at most two maker identities. A visible fixed order book is a smaller feasible set: an order has one actual owner, is not a freely divisible score mass, and quantity/price increments, minimum qualifying size, maker identities, and available capital or inventory may constrain constructions. Reassigning a whole already-qualified order preserves its score only when all inputs and eligibility remain fixed. Splitting an order can destroy eligibility or change the adjusted midpoint, so holding A,B constant then requires justification. Do not conflate exchange minimum accepted order size with the reward minimum qualifying size.

Counterexample to endpoint attainability for indivisible existing orders: one eligible score atom (1,0) and one (0,1). A=B=1. Group them together: score 1. Keep owners separate: score 2/3. These are the only partition outcomes. The relaxed lower bound 1/2 cannot be reached. This does not refute the inequality, only an unrestricted attainability claim about real lots. It is a mathematical atom example, not a claim about a specific live market's settings.

## Own maker and denominator

If A,B are competitor-only totals and own maker score q>0 is fixed under the same scoring state, then q/(q+U)<=own sample share<=q/(q+L). Including q in A,B and adding it again double-counts. If A,B instead cover everyone, use total denominator bounds without adding q, and recognize that fixing one's maker components reduces the feasible set and may destroy tightness. Existing and newly proposed own orders must first be aggregated by actual maker before f is applied: f(x+u,y+v) is generally not f(x,y)+f(u,v). For example (1,0) and (0,1) together score 1, versus 2/3 if incorrectly treated as two makers.

q=0 with positive denominator means zero share. All-zero denominator is undefined by the displayed fractions; a production convention cannot be invented. Positive q with zero competitor mass has share 1. Adding an own quote can affect size-adjusted midpoint, all competitors' weights, eligibility, and interval membership; a bound keeping those frozen is conditional, not an unconditional intervention result.

## Epoch and money

Bounds should first be calculated at each sample with that sample's parameters and branch. With a common set of positive-denominator samples, the final normalized epoch share is the arithmetic mean of sample shares; summing per-sample bounds and dividing by the same count preserves bounds. Do not replace this with a ratio of pooled raw scores: synthetic samples (q,r)=(1,1),(1,9) give mean share 3/10, but pooled-score ratio 1/6. Do not assume every epoch necessarily has 1,440 usable positive-denominator samples. Handling absent/zero-total samples must be verified separately. No pointwise score bound, even tight, establishes a realized dollar payout, future reward allocation, or positive net economics.

## Reproducible tests

Run `python validate.py` in this directory. results.json records:
- 5,202 exact rational endpoint constructions.
- 242 LP extrema (min/max over a finite set of rays including all analytic witnesses), matching the formulas.
- 20,000 random exact-rational partitions with no bound violation.
- Exact indivisible-atom and epoch-aggregation counterexamples.

The LP and tests corroborate, but do not replace, the universal proof. All inputs are bounded synthetic values.
