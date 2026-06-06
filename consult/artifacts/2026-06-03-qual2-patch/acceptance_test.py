from src.postflop import decide_postflop as dp
from src.equity import equity_vs_range
from src.postflop import PRIOR_RANGE_TIGHT
def S(**k):
    base=dict(can_check=False, your_bet_this_street=0, seat_to_act=4,
              players=[{"seat":4},{"seat":0,"is_folded":False,"state":"active"}])
    base.update(k); return base
cases={
 "1_hand65_8d3d_nonnut(LEAK->fold)": S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["8d","3d"],community_cards=["Qd","Kd","Td","Qh","Ah"]),
 "2_nut_control_AdJd(->commit)":     S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["Ad","Jd"],community_cards=["Qd","Kd","Td","Qh","Ah"]),
 "3_safe_small_AA(->raise)":         S(pot=300,your_stack=10000,amount_owed=150,current_bet=150,
        street="flop",your_cards=["Ah","Ad"],community_cards=["Kc","7d","2s"]),
 "4_safe_bigcommit_KKset(->commit)": S(pot=6000,your_stack=10000,amount_owed=5000,current_bet=5000,
        street="flop",your_cards=["Kh","Ks"],community_cards=["Kc","7d","2s"]),
 "5_hand269_Kflush_4club(LEAK->fold)":S(pot=8000,your_stack=25000,amount_owed=7000,current_bet=7195,
        your_bet_this_street=2712,street="river",your_cards=["Kc","4h"],
        community_cards=["7c","9c","2c","5c","3s"]),
 "6_boat_on_pairedflush(->commit)":  S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["Qc","Qs"],community_cards=["Qd","Kd","Td","Td","Ah"]),
}
for name,st in cases.items():
    es=equity_vs_range(st["your_cards"],st["community_cards"],PRIOR_RANGE_TIGHT,trials=180)
    a=dp(dict(st))
    print(f"{name:36s} eq_strong={es:.2f} -> {a}")
