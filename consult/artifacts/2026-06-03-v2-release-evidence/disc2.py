import sys, json, random
random.seed(7)
try:
    import numpy as _np; _np.random.seed(7)
except Exception: pass
BOT_ROOT = sys.argv[1]; LABEL = sys.argv[2]
sys.path.insert(0, BOT_ROOT)
from src.equity import equity_vs_range
from src.postflop import decide_postflop, PRIOR_RANGE_TIGHT
def S(**k):
    base=dict(can_check=False, your_bet_this_street=0, seat_to_act=4,
              players=[{"seat":4},{"seat":0,"is_folded":False,"state":"active"}])
    base.update(k); return base
# medium made hand (top pair weak kicker) on a SAFE board; vary owed_frac across the
# 0.25 (V2 can_call_large cap) and 0.40 (patch commit_frac) cliffs.
def spot(owed_frac):
    stack=10000; owed=int(owed_frac*stack)
    return S(pot=2000,your_stack=stack,amount_owed=owed,current_bet=owed,
             street="river",your_cards=["Qc","9c"],community_cards=["Qd","7s","2c","Th","4h"])
SPOTS={f"priced_owed{int(f*100):02d}pct": spot(f) for f in (0.12,0.20,0.30,0.35)}
out={"label":LABEL,"spots":{}}; counts={"fold":0,"call":0,"raise":0,"all_in":0,"check":0}
for name,st in SPOTS.items():
    eqs=equity_vs_range(st["your_cards"],st["community_cards"],PRIOR_RANGE_TIGHT,trials=400)
    act=decide_postflop(dict(st)); a=act.get("action","?"); counts[a]=counts.get(a,0)+1
    out["spots"][name]={"owed_frac":round(st["amount_owed"]/st["your_stack"],2),
                        "eq_strong":round(eqs,3),"action":act}
out["counts"]=counts
print(json.dumps(out,indent=1))
