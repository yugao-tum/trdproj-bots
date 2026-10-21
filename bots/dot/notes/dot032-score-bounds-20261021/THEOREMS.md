# Exact aggregate-score envelopes, not reward identification

Scope: one offline mathematical diagnostic inside dot-032 evidence-readiness. Date: 2026-10-21. No new mechanism, market selection, forward start, PLAN, API acquisition, transaction, credential, or remote edit. All numerical examples are synthetic. This is independently derived from cached official equations, not another bot's rule set.

## Source and interpretation

Official source: https://docs.polymarket.com/programs/liquidity-rewards . Cached official source consulted at source lines 166–243; source hash is in SOURCES.json. Source line 182 says c is currently 3.0; the conclusions below condition on c=3, not on verifying a live setting. Source lines 208 and 215 define complementary score sides: side A is bids in outcome m plus asks in its complement m'; side B is asks in m plus bids in m'. Thus A/B are not merely the bid/ask totals of one outcome. Each eligible order contributes size times b((v−s)/v)^2. Eligibility, adjusted midpoint, spread units and multiplier must be correct before adding scores. The cached Market Details source at source lines 640 onward, specifies minimum qualifying order size and spread. Order-execution minimum notional and reward minimum share quantity are different constraints.

Only the latest restricted 06:20 UTC review evidence was used for governance/context. No other bot's strategy or old crypto results were used. Cached documentation is the stipulated formula source, not evidence that present live parameters or implementation are verified.

## Conditions

At one actual scoring instant in one market, let each competing maker i have nonnegative eligible side scores (a_i,b_i), with A=sum a_i, B=sum b_i. Exclude our own orders from these totals. All makers share the same scoring regime and correctly determined size-cutoff-adjusted midpoint. Include both complementary books without duplicating an order. The population must include all scoring competition, not only a depth-limited or stale subset. The sum is over maker identities under the official reward aggregation rule, not arbitrary order IDs.

The results hold for any finite grouping of nonnegative scores. Sharpness claims are relative to the relaxed information set containing only A and B: arbitrary nonnegative per-maker allocations are admissible. For a fixed known order multiset, per-order size thresholds, indivisible orders, known identity constraints or bounds on maker count can prevent attaining an endpoint. Such restrictions can tighten the interval, but never invalidate the enclosing bounds. A claim that the bounds are *sharp for a specific real book* requires an admissible partition of its eligible orders. No invented ability to split another maker's orders is assumed. For example, with exactly one indivisible score-1 order on each side, the only maker partitions yield D=2/3 (separate makers) or D=1 (one maker), never the relaxed lower bound 1/2.

## Theorem 1: interior midpoint, exact relaxed envelope

For adjusted midpoint in [0.10,0.90], define
f(a,b)=max(min(a,b), a/3, b/3), D=sum_i f(a_i,b_i).
Then
L(A,B)=max(A/3, B/3, (A+B)/4) <= D <= U(A,B)=min(A,B)+|A−B|/3.
These are the best possible bounds using only A,B over the relaxed class.

Proof of lower bound: f>=a/3 and f>=b/3. Also f>=(a+b)/4. To see the last inequality assume a>=b. If a>=3b, f=a/3>=(a+b)/4; otherwise f=b>=(a+b)/4. Sum these three inequalities separately.

Lower endpoint construction: if A>=3B, a single maker (A,B) has D=A/3=L; if B>=3A, use its symmetric counterpart. Otherwise let t=(3A−B)/8 and z=(3B−A)/8, both nonnegative. Two makers (3t,t) and (z,3z) sum to (A,B) and have scores t,z, so D=t+z=(A+B)/4=L. Omit zero-score makers.

Proof of upper bound: pointwise f(a,b)<=(a+b+min(a,b))/3. For a>=b, if a>=3b then f=a/3<=(a+2b)/3; otherwise f=b<=(a+2b)/3 since a>=b. Sum and use sum min(a_i,b_i)<=min(A,B), obtaining (A+B+min(A,B))/3=U.

Upper endpoint construction: if A>=B, makers (B,B) and (A−B,0) give D=B+(A−B)/3=U; use symmetry if B>=A.

At A=B=100 the sharp interval is [50,100], not [66 2/3,100]. The latter lower number comes from only the two single-sided-maker construction and is not a universal minimum.

## Theorem 2: extreme midpoint

For adjusted midpoint in [0,0.10) or (0.90,1], f_ext(a,b)=min(a,b). Then 0<=D<=min(A,B), with relaxed endpoints attained by separate one-sided makers (A,0),(0,B), and one combined maker (A,B), respectively. A zero aggregate on either side forces D=0. The interior rule includes exactly 0.10 and 0.90. Do not smooth over these boundary switches.

## Corollary: own instantaneous normalized share

Let our eligible scores be x,y and q=f(x,y) in the applicable regime. For q>0 and exact competing A,B,
q/(q+U) <= r=q/(q+D) <= q/(q+L).
Use L=0,U=min(A,B) in the extreme regime. The own score belongs in the denominator exactly once. If supplied A_total,B_total already contain ours, first subtract x,y; do not apply the bound to all totals and then add q again. For q=0 and D>0, r=0. For q=D=0 the official fractional formula is 0/0; this report does not invent a zero-denominator allocation convention.

A target instantaneous share h in (0,1) is guaranteed across all admissible competing groupings if q>=h U/(1−h). In the relaxed class a share of at least h is possible only if q>=h L/(1−h), and possible when that inequality holds. This is a mathematical conditional screen, not a quoting instruction or capital recommendation.

Synthetic A=B=100: our (30,30) gives q=30 and r in [3/13,3/8], approximately [23.08%,37.50%]. Our (30,0) gives q=10 and r in [1/11,1/6], approximately [9.09%,16.67%]. At an extreme midpoint our one-sided quote has q=0, while a balanced q=30 gives r in [3/13,1]. These compare stated scores, not equal capital or equal inventory risk.

## Why one aggregated competing maker is not a one-direction bias

For balanced A=B=100, f(A,B)=100=U, but true D can be 50. Treating all competition as one maker can overstate D and understate our share.

For A=300,B=100, f(A,B)=100=L, but makers (100,100),(200,0) give D=500/3=U. It can instead understate D and overstate our share. Thus there is no universal 'conservative' direction for the aggregate-one-maker shortcut. Both examples have nonnegative eligible synthetic scores.

## Visible L2, thresholds and weakened evidence

Even complete raw price-level quantities are not necessarily eligible A,B. A level totaling 100 shares can contain one qualifying 100-share order or two ineligible 50-share orders when the minimum per order is 100. It can therefore retain identical L2 while eligible score changes from positive to zero. The exact eligibility rule and order decomposition matter; this example uses the documented per-order threshold interpretation. Likewise incomplete complementary books, stale state, unknown adjusted midpoint or unknown multiplier invalidate pretending the inputs are exact.

If A_raw,B_raw are known upper bounds on *all* eligible competing side scores under a fixed verified midpoint/weight rule, nonnegative weights imply A<=A_raw, B<=B_raw. Since U is coordinatewise nondecreasing, 0<=D<=U(A_raw,B_raw) in the interior; at extremes 0<=D<=min(A_raw,B_raw). Thus a weaker but still rigorous positive instantaneous share floor q/(q+U_raw) survives unknown order eligibility when q>0 is independently certified. The upper share bound can become 1. The interior L evaluated on raw totals is NOT justified.

A depth-limited visible subset supplies no finite upper bound on unseen competition: add arbitrary eligible hidden/unobserved depth. Therefore it yields no positive robust own-share floor without a separate upper bound on omitted eligible scores. This is lack of coverage, not a defect in Theorem 1. Conversely, if weights cannot be evaluated but one certifies a multiplier bound b_max and full eligible-range size totals V_A,V_B with 0<=s<=v, S<=b_max gives A<=b_max V_A and B<=b_max V_B. This coarser ceiling is conditional and not available from an unspecified or incomplete snapshot.

## Hypothetical own-quote effect, queue and time

All own-share comparisons hold the competing score population and scoring midpoint/parameters fixed. Inserting our quote may change the size-cutoff-adjusted midpoint and therefore competitors' weights or even switch the regime; in that case recompute A,B,x,y at the *post-insertion* state. The current-book bound is not automatically a counterfactual bound. As a discontinuity example, our one-sided positive q inside the interior becomes zero just outside the permitted interval.

Queue rank is absent from this reward equation. Equal eligible price/size/state gives the same instantaneous score regardless of queue position. Queue affects whether and how much of an order remains resting, fills and adverse-selection exposure, hence future q and costs; it does not justify an unobserved fill, assured resting time, or reward claim. Hypothetical cancellation/fill changing own (30,30) to (30,0) reduces q from 30 to 10 in the interior and from 30 to 0 at an extreme, even if the surviving side's queue improves. A touch is not proof of a fill.

## Sampling, epoch normalization, cash and profit: separate obligations

The source describes random-offset minute sampling and an epoch sum, followed by epoch renormalization. If the *actual set* of valid samples J is known, each sample has positive total score, all competitors are included, and the source's sample sums are the implementation, then sum_i r_i,u=1 and sum_i Q_epoch,i=|J|. The final share is the arithmetic mean of our actual instantaneous shares across J. In that special case, sample-wise certified bounds l_u<=r_u<=h_u imply average(l_u)<=Q_final<=average(h_u). Include zero own shares at valid samples when absent. Do not use ratio of aggregate daily Q scores in place of mean normalized shares.

A snapshot cannot establish that mean. Even an exactly calculated positive snapshot-state share at an observation not known to be an official sample is consistent with disappearance before every actual sampled instant; absent a coverage/resting-time guarantee, the epoch lower bound remains zero. With the same one observed state, a world with persistent quoting and a world with no later eligible quote produce different epoch shares. Hourly snapshots do not identify random minute samples. A uniform guaranteed bound at all possible sampling times would suffice, but is not supplied here. Undefined zero-total samples require verified implementation handling before the averaging corollary applies.

Reward pool validity, allocations, epoch coverage, actual own eligibility and the payout threshold's aggregation scope are not established. The source states a $1 payout minimum but does not settle its aggregation scope here. Consequently a positive conditional score-share bound is not a guaranteed payable dollar amount. Fees, inventory, exit cost, capital commitment, fills, adverse selection and losses are also absent. No claim of profitability, observed profit, forward evidence, or score/review readiness follows.

## Decision

The earlier grouping gap is partly quantifiable: exact eligible aggregates permit sharp instantaneous bounds, and even complete raw upper-envelope aggregates can yield a conservative floor conditional on certified own q. Maker IDs are not logically necessary for *some bounded instantaneous statement*. They remain necessary for exact identification absent equivalent official score data. The actual input/coverage/eligibility/random-sample/payment/cost and publication-sequencing gates are unresolved. Maintain dot-032 STOP; do not start a forward run or mark a positive/negative economic result.

## Own-maker aggregation clarification
Existing and proposed own orders must be combined by actual maker before applying f: f(x+u,y+v) need not equal f(x,y)+f(u,v). For example (1,0) plus (0,1) has combined score 1, not 2/3. The own score q is the complete same-maker aggregate in the same post-insertion state.
