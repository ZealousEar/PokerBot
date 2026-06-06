import sys, json, random
random.seed(42)
try:
    import numpy as _np; _np.random.seed(42)
except Exception:
    pass
BOT_ROOT = sys.argv[1]
LABEL = sys.argv[2]
sys.path.insert(0, BOT_ROOT)

from src.equity import equity_vs_range
from src.postflop import decide_postflop, PRIOR_RANGE_TIGHT

# optional gate introspection
def gate_info(hole, board, eqs):
    info = {}
    try:
        from src.commitment import can_commit_raise
        info["gate"] = "commitment.can_commit_raise"
        info["can_commit"] = bool(can_commit_raise(hole, board, eqs))
    except Exception:
        try:
            from src.postflop import _can_commit
            info["gate"] = "postflop._can_commit"
            info["can_commit"] = bool(_can_commit(hole, board, eqs))
        except Exception:
            info["gate"] = "none(baseline-no-gate)"
            info["can_commit"] = None
    try:
        from src.hand_features import classify_hand
        info["full_house_or_better"] = bool(classify_hand(hole, board).get("full_house_or_better"))
    except Exception:
        info["full_house_or_better"] = None
    return info

def S(**k):
    base=dict(can_check=False, your_bet_this_street=0, seat_to_act=4,
              players=[{"seat":4},{"seat":0,"is_folded":False,"state":"active"}])
    base.update(k); return base

SPOTS = {
 # ---- acceptance (criteria 1 & 2) ----
 "A1_hand65_8d3d_nonnut(leak->fold)": S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["8d","3d"],community_cards=["Qd","Kd","Td","Qh","Ah"]),
 "A2_nut_AdJd(->commit)": S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["Ad","Jd"],community_cards=["Qd","Kd","Td","Qh","Ah"]),
 "A3_safe_small_AA(->raise)": S(pot=300,your_stack=10000,amount_owed=150,current_bet=150,
        street="flop",your_cards=["Ah","Ad"],community_cards=["Kc","7d","2s"]),
 "A4_safe_bigcommit_KKset(->commit)": S(pot=6000,your_stack=10000,amount_owed=5000,current_bet=5000,
        street="flop",your_cards=["Kh","Ks"],community_cards=["Kc","7d","2s"]),
 "A5_hand269_Kflush_4club(leak->fold)": S(pot=8000,your_stack=25000,amount_owed=7000,current_bet=7195,
        your_bet_this_street=2712,street="river",your_cards=["Kc","4h"],
        community_cards=["7c","9c","2c","5c","3s"]),
 "A6_boat_on_pairedflush(->commit)": S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["Qc","Qs"],community_cards=["Qd","Kd","Td","Td","Ah"]),
 # ---- DISCRIMINATOR: dominated boats (Task-4 warning #5) ----
 "D1_dominated_Qfull_Qc9h(want FOLD)": S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["Qc","9h"],community_cards=["Kd","Ks","Qs","Qd","5c"]),
 "D2_underboat_777_7s7h(want FOLD)": S(pot=12000,your_stack=24000,amount_owed=12000,current_bet=12000,
        street="river",your_cards=["7s","7h"],community_cards=["Kd","Ks","7c","2h","3d"]),
 # ---- criterion 4: non-nut flush on a PAIRED board ----
 "C4_nonnut_flush_pairedboard(want FOLD)": S(pot=9000,your_stack=20000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["Kd","Qd"],community_cards=["5d","5h","2d","9d","Ts"]),
}

out = {"label": LABEL, "bot_root": BOT_ROOT, "spots": {}}
counts = {"fold":0,"call":0,"raise":0,"all_in":0,"check":0}
large_commit = 0
for name, st in SPOTS.items():
    eqs = equity_vs_range(st["your_cards"], st["community_cards"], PRIOR_RANGE_TIGHT, trials=400)
    act = decide_postflop(dict(st))
    a = act.get("action","?")
    counts[a] = counts.get(a,0)+1
    stack = st["your_stack"]; owed = st["amount_owed"]
    amt = act.get("amount", 0)
    committed = (a in ("raise","all_in") and max(amt, owed) >= 0.40*stack) or (a=="call" and owed >= 0.40*stack)
    if committed: large_commit += 1
    gi = gate_info(st["your_cards"], st["community_cards"], eqs)
    out["spots"][name] = {"eq_strong": round(eqs,3), "action": act, "committed_ge40pct": committed, **gi}
out["counts"] = counts
out["large_commit_count"] = large_commit
print(json.dumps(out, indent=1))
