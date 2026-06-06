import sys, json, random
BOT_ROOT = sys.argv[1]; LABEL = sys.argv[2]
sys.path.insert(0, BOT_ROOT)
from src.equity import equity_vs_range
from src.postflop import PRIOR_RANGE_TIGHT
def gate(hole, board, eq):
    try:
        from src.commitment import can_commit_raise
        return can_commit_raise(hole, board, eq)
    except Exception:
        from src.postflop import _can_commit
        return _can_commit(hole, board, eq)
BOARDS = {
 "C4_nonnut_flush_PAIRED(KdQd|5d5h2d9dTs)": (["Kd","Qd"], ["5d","5h","2d","9d","Ts"]),
 "C3_NUTflush_PAIRED(AdQd|5d5h2d9dTs)":     (["Ad","Qd"], ["5d","5h","2d","9d","Ts"]),
 "D1_dominated_Qfull(Qc9h|KdKsQsQd5c)":     (["Qc","9h"], ["Kd","Ks","Qs","Qd","5c"]),
}
sweep = [0.50,0.55,0.60,0.70,0.79,0.80,0.85,0.90,0.91,0.92,0.95,0.99]
print(f"==== {LABEL} ({BOT_ROOT}) ====")
for name,(hole,board) in BOARDS.items():
    eqs = []
    for s in (11,22,33):
        random.seed(s)
        try:
            import numpy as _np; _np.random.seed(s)
        except Exception: pass
        eqs.append(equity_vs_range(hole, board, PRIOR_RANGE_TIGHT, trials=2000))
    measured = sum(eqs)/len(eqs)
    decisions = {f"{e:.2f}": ("COMMIT" if gate(hole,board,e) else "fold") for e in sweep}
    # find the threshold (lowest eq that commits)
    commits = [e for e in sweep if gate(hole,board,e)]
    thr = min(commits) if commits else None
    print(f"\n{name}")
    print(f"  measured eq_strong (3 seeds x2000): {[round(x,3) for x in eqs]}  mean={measured:.3f}")
    print(f"  commit threshold (min eq that commits): {thr}")
    print(f"  sweep: " + "  ".join(f"{k}:{'C' if v=='COMMIT' else 'f'}" for k,v in decisions.items()))
