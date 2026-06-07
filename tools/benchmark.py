"""Benchmark — runs N hands vs reference opponents (G2/G3) or against the
game-theoretic verification suites (G5) and reports bb/100 with bootstrap
95 % CIs.

Modes:
    Single opponent:   --opponent <name> --hands N
    All reference:     --all-templates --hands N --min-bb 15
    Overlay ablation:  --ablate-overlay --hands N --min-bb 3
    Self-play ratchet: --self-play --vs-prior --min-bb 3

Variance and final selection
============================
At 10k hands, bb/100 variance is ~20 bb/100 (95 % CI). Selecting between
candidate bots on a single 10k run selects noise. For ratchet, ablation,
and branch-arbitration selection use paired seeds:

  - Fix a seed schedule: seed = base, base+1, ... base+K-1 (default K=10).
  - Both candidates play the same K matches against the same opponent
    lineup; we compare paired EV deltas (variance drops ~5-10x).
  - The --paired-seed-base flag activates this mode; pass through the
    seed to ext/fullhouse-engine/sandbox/match.py.

For G3 all-templates acceptance, either use --paired-seed-base K=10 with
--hands 10000, OR bump --hands to >= 50000. Never declare a gate green
on a single 10k run without paired-seed support.
"""
import argparse
import sys

# All five reference bots in ext/fullhouse-engine/bots/.
TEMPLATES = ("template", "aggressor", "mathematician", "shark", "ref_bot_2")

# Biased-opponent suite for --ablate-overlay (synthetic seats; see
# tests/integration/test_biased_opponents.py at G5).
BIASED_SUITE = ("tight_passive", "loose_passive", "tight_aggressive", "loose_aggressive")

# Prior gate snapshots checked by --self-play --vs-prior.
PRIOR_SNAPSHOTS = (
    "submissions/v0_wired.zip",
    "submissions/v1_blueprint.zip",
    "submissions/v2_postflop.zip",
    "submissions/v3_hardened.zip",
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--opponent", help="Single opponent in ext/fullhouse-engine/bots/")
    p.add_argument("--all-templates", action="store_true",
                   help="Run vs all five reference bots")
    p.add_argument("--ablate-overlay", action="store_true",
                   help="G5: with-overlay vs blueprint-only on the biased-opponent suite")
    p.add_argument("--self-play", action="store_true",
                   help="G5: v_final vs prior gate snapshots")
    p.add_argument("--vs-prior", action="store_true",
                   help="Modifier for --self-play; targets PRIOR_SNAPSHOTS")
    p.add_argument("--hands", type=int, default=10000)
    p.add_argument("--min-bb", type=float, default=0.0,
                   help="Exit nonzero if any margin falls below this threshold")
    p.add_argument("--paired-seed-base", type=int, default=None,
                   help="Activate paired-seed comparison. Runs K matches at "
                        "seeds [base, base+1, ..., base+K-1]; the implementer "
                        "must run both candidate bots against the same opponent "
                        "lineup at each seed and compare paired EV deltas. "
                        "Required for ratchet, ablation, and branch-arbitration "
                        "comparisons -- see docstring.")
    p.add_argument("--paired-seed-count", type=int, default=10,
                   help="K for --paired-seed-base (default 10).")
    args = p.parse_args()

    if args.all_templates:
        targets = list(TEMPLATES)
    elif args.ablate_overlay:
        # TODO (G5): for each biased seat in BIASED_SUITE, run hands of with-overlay
        # and blueprint-only, report (with - blueprint) margin per seat.
        print(f"TODO (G5): ablate overlay over {len(BIASED_SUITE)} biased seats × {args.hands} hands; --min-bb {args.min_bb}")
        return 0
    elif args.self_play and args.vs_prior:
        # TODO (G5): for each prior snapshot, run v_final vs prior, report margin.
        print(f"TODO (G5): self-play v_final vs {len(PRIOR_SNAPSHOTS)} prior snapshots × {args.hands} hands; --min-bb {args.min_bb}")
        return 0
    elif args.opponent:
        targets = [args.opponent]
    else:
        p.error("Specify --opponent, --all-templates, --ablate-overlay, or --self-play --vs-prior")

    # TODO (G2): for each target, run args.hands via sandbox/match.py, collect
    # per-hand chip deltas, compute bb/100 + bootstrap 95% CI. Exit 1 if any
    # target's lower CI bound < args.min_bb.
    for t in targets:
        print(f"TODO (G2/G3): benchmark {args.hands} hands vs {t}; --min-bb {args.min_bb}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
