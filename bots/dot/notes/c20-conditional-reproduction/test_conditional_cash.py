import unittest
from decimal import Decimal as D
import conditional_cash_v1_1 as m

SYM=m.SYMBOLS[0]
def bar(o='100',h=None,l=None,c=None):
    o=D(str(o));c=o if c is None else D(str(c));h=max(o,c) if h is None else D(str(h));l=min(o,c) if l is None else D(str(l))
    return {'open':o,'high':h,'low':l,'close':c}
def fixture(signal='103',S0='100',F0='103',S1='110',F1='110.5',mark='103',spotclose='100'):
    e,s,en,ex,days=m.required_dates(SYM)
    spot={m.ds(s):bar('100'),m.ds(en):bar(S0),m.ds(ex):bar(S1)}
    trade={(SYM,m.ds(s)):bar(signal),(SYM,m.ds(en)):bar(F0),(SYM,m.ds(ex)):bar(F1)}
    marks={}
    for day in days:
        spot.setdefault(m.ds(day),bar(spotclose));marks[SYM,m.ds(day)]=bar(mark)
    marks[SYM,m.ds(ex)]=bar(mark)
    return m.Data(spot,trade,marks)
class Tests(unittest.TestCase):
    def test_hand_ledger_both_entry_fees_and_release(self):
        # q=12, M0=1236; initial fees3.6+3.708; reserve56.692.
        x=m.initial_accounts('100','103','.003')
        self.assertEqual(D(12),x['q']);self.assertEqual(D(1236),x['initial_future_collateral'])
        self.assertEqual(D('1203.6'),x['spot_wallet_preplaced']);self.assertEqual(D('1239.708'),x['future_wallet_preplaced']);self.assertEqual(D('56.692'),x['venue_reserve'])
        y=m.exit_accounts(x,'100','103','110','110.5','.003')
        self.assertEqual(D(120),y['spot_gross_change']);self.assertEqual(D(-90),y['future_gross_change'])
        self.assertEqual(D('3.96'),y['spot_exit_fee']);self.assertEqual(D('3.978'),y['future_exit_fee'])
        self.assertEqual(D('1142.022'),y['future_wallet_after_exit']);self.assertEqual(D('1316.04'),y['spot_wallet_after_exit'])
        self.assertEqual(D('15.246'),y['total_four_side_cost']);self.assertEqual(D('14.754'),y['algebraic_net_cash_change']);self.assertEqual(D('5014.754'),y['algebraic_final_cash'])
    def test_stress_same_quantity_actual_costs(self):
        d=fixture();b,_=m.simulate_episode(d,SYM,'base',D('.003'));s,_=m.simulate_episode(d,SYM,'stress',D('.006'))
        self.assertEqual(b['q'],s['q']);self.assertEqual(D('30.492'),s['total_four_side_cost']);self.assertEqual(D('-.492'),s['conditional_net_cash_change'])
        self.assertEqual(s['conditional_change_divided_by_5000'],D('-.492')/D(5000))
    def test_actual_notionals_not_flat_four_times_1200(self):
        r,_=m.simulate_episode(fixture(),SYM,'base',D('.003'))
        self.assertEqual(D('15.246'),r['total_four_side_cost']);self.assertNotEqual(D('14.4'),r['total_four_side_cost'])
    def test_budget_marginal_threshold(self):
        c=D('.003');Fmax=(D(2500)/(1+c)-D(1200))/D(12)
        x=m.initial_accounts('100',Fmax,c)
        self.assertLess(abs(x['venue_reserve']),D('1e-40'))
        self.assertGreater(m.initial_accounts('100',Fmax-D('.01'),c)['venue_reserve'],0)
        self.assertLess(m.initial_accounts('100',Fmax+D('.01'),c)['venue_reserve'],0)
    def test_budget_fail_no_resize_or_borrow(self):
        r,d=m.simulate_episode(fixture(F0='110'),SYM,'base',D('.003'))
        self.assertEqual('initial_capital_infeasible',r['status']);self.assertEqual(D(12),r['q']);self.assertFalse(r['position_entered']);self.assertIsNone(r['conditional_net_cash_change']);self.assertEqual([],d)
    def test_signal_strict_and_previous_day(self):
        d=fixture(signal='101.7');e,s,en,ex,days=m.required_dates(SYM);d.trade[SYM,m.ds(en)]['close']=D(999)
        r,di=m.simulate_episode(d,SYM,'base',D('.003'))
        self.assertFalse(r['signal_triggered']);self.assertEqual(D(0),r['conditional_net_cash_change']);self.assertFalse(r['position_entered']);self.assertEqual([],di)
    def test_no_open_basis_recheck(self):
        r,_=m.simulate_episode(fixture(signal='103',F0='100'),SYM,'base',D('.003'))
        self.assertTrue(r['signal_triggered']);self.assertTrue(r['position_entered']);self.assertEqual(D(1200),r['future_entry_notional'])
    def test_fixed_89_days_excludes_exit_high_and_expiry(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM)
        d.mark[SYM,m.ds(ex)]['high']=D(100000)
        d.mark[SYM,m.ds(e)]=bar('100000')
        r,di=m.simulate_episode(d,SYM,'base',D('.003'))
        self.assertEqual(89,len(di));self.assertEqual(m.ds(en),di[0]['date']);self.assertEqual(m.ds(ex-m.timedelta(days=1)),di[-1]['date']);self.assertEqual(D(1236),r['minimum_observed_future_equity_high_or_boundary'])
    def test_entry_high_included(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM);d.mark[SYM,m.ds(en)]['high']=D(150)
        r,_=m.simulate_episode(d,SYM,'base',D('.003'))
        self.assertEqual(D(672),r['minimum_observed_future_equity_high_or_boundary'])
    def test_daily_nav_opening_cost_only_not_exit_cost(self):
        r,di=m.simulate_episode(fixture(),SYM,'base',D('.003'))
        self.assertEqual(D('4992.692'),di[0]['daily_nav_proxy_close']);self.assertEqual(D(1236),di[0]['future_cash_collateral'])
    def test_observed_nonpositive_equity_fails_no_rescue(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM);d.mark[SYM,m.ds(days[20])]['high']=D(206)
        r,_=m.simulate_episode(d,SYM,'base',D('.003'))
        self.assertEqual('known_cash_path_infeasible',r['status']);self.assertIsNone(r['conditional_net_cash_change']);self.assertEqual(D('56.692'),r['venue_reserve'])
    def test_exit_future_cash_shortfall_cannot_use_spot(self):
        r,_=m.simulate_episode(fixture(S1='1000',F1='210'),SYM,'base',D('.003'))
        self.assertEqual('exit_future_cash_infeasible',r['status']);self.assertLess(r['future_wallet_after_exit'],0);self.assertGreater(r['spot_wallet_after_exit'],10000);self.assertIsNone(r['conditional_net_cash_change'])
    def test_mark_missing_not_zero_filled(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM);missing=m.ds(days[5]);del d.mark[SYM,missing]
        r,di=m.simulate_episode(d,SYM,'base',D('.003'))
        self.assertFalse(r['active_mark_path_complete']);self.assertFalse(r['margin_survival_verified']);self.assertIn(missing,r['source_quality']['holding_mark_missing_dates'])
        dr=next(x for x in di if x['date']==missing);self.assertIsNone(dr['future_equity_mark_close']);self.assertIsNone(dr['daily_nav_proxy_close'])
        self.assertEqual(D('14.754'),r['conditional_net_cash_change']) # Explicit survival-conditioned algebra, with incomplete-path flag.
    def test_missing_signal_not_cash_zero(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM);del d.spot[m.ds(s)]
        r,_=m.simulate_episode(d,SYM,'base',D('.003'));self.assertEqual('missing_signal_data',r['status']);self.assertIsNone(r['conditional_net_cash_change'])
    def test_missing_entry_not_cash_zero(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM);del d.trade[SYM,m.ds(en)]
        r,_=m.simulate_episode(d,SYM,'base',D('.003'));self.assertEqual('missing_entry_price',r['status']);self.assertIsNone(r['conditional_net_cash_change'])
    def test_missing_exit_does_not_change_entry_signal(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM);del d.trade[SYM,m.ds(ex)]
        r,_=m.simulate_episode(d,SYM,'base',D('.003'));self.assertEqual('missing_exit_price',r['status']);self.assertTrue(r['position_entered']);self.assertIsNone(r['conditional_net_cash_change'])
    def test_missing_unused_exit_valid_cash_only(self):
        d=fixture(signal='101');e,s,en,ex,days=m.required_dates(SYM);del d.trade[SYM,m.ds(ex)]
        r,_=m.simulate_episode(d,SYM,'base',D('.003'));self.assertEqual('cash_only_signal_not_triggered',r['status']);self.assertEqual(D(0),r['conditional_net_cash_change'])
    def test_same_start_each_episode_no_compounding(self):
        data=fixture();records,_=m.evaluate(data)
        self.assertEqual(16,len(records));self.assertEqual({D(5000)},{r['initial_nav'] for r in records});self.assertIsNone(records[2]['conditional_net_cash_change'])
    def test_unknown_margin_and_execution_never_pass(self):
        r,_=m.simulate_episode(fixture(),SYM,'base',D('.003'))
        for k in ['margin_survival_verified','execution_verified','historical_actual_fee_verified','quantity_filters_verified','unseen_oos']:self.assertFalse(r[k])
    def test_floating_gains_breach_dynamic_venue_cap(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM)
        d.spot[m.ds(days[10])]=bar('110')
        d.mark[SYM,m.ds(days[10])]=bar('110.5')
        r,di=m.simulate_episode(d,SYM,'base',D('.003'))
        point=next(x for x in di if x['date']==m.ds(days[10]))
        self.assertEqual(D('2522.692'),point['daily_venue_mtm_proxy']);self.assertTrue(point['daily_venue_over_2500'])
        self.assertTrue(r['capital_gate_failed']);self.assertFalse(r['capital_gate_verified'])
        self.assertGreater(r['venue_over_2500_point_count'],0);self.assertEqual(D('14.754'),r['conditional_net_cash_change'])
        self.assertEqual(D('2514.754'),r['exit_after_close_venue_cash_conditional']);self.assertTrue(r['exit_after_close_venue_over_2500'])
    def test_dynamic_missing_point_not_pass(self):
        d=fixture();e,s,en,ex,days=m.required_dates(SYM);del d.mark[SYM,m.ds(days[12])]
        r,_=m.simulate_episode(d,SYM,'base',D('.003'))
        self.assertIn(m.ds(days[12])+':daily_close',r['venue_mtm_missing_points']);self.assertFalse(r['capital_gate_verified'])
    def test_no_breach_still_not_intraday_verified(self):
        r,_=m.simulate_episode(fixture(S1='100',F1='103'),SYM,'base',D('.003'))
        self.assertFalse(r['capital_gate_failed']);self.assertFalse(r['capital_gate_verified']);self.assertEqual('unknown_unverified_intraday_maximum',r['capital_gate_status'])
    def test_timestamp_units_and_duplicate_guard(self):
        self.assertEqual(m.normalized_date('1735603200000'),m.normalized_date('1735603200000000'))
        x={};m.unique_put(x,'day',1)
        with self.assertRaises(ValueError):m.unique_put(x,'day',2)
if __name__=='__main__':unittest.main(verbosity=2)
