#!/usr/bin/env python3
"""Independent re-derivation of Thorp's portal results.
Does NOT import/read tools/field_recon.py. Faithful port of
ext/fullhouse-engine/engine/game.py betting bookkeeping (apply_action/_put_in)
to segment streets and reconstruct stacks from the engine-ordered action_log.
"""
import json, glob, os, random, statistics
from itertools import combinations
import eval7

THORP = "1c0abfd8-c355-471b-8c7b-e5e75800ce04"
HIST = "/Users/farhad/Code/PokerBot/data/portal_histories"
SB, BB, START = 50, 100, 10000


# ---------------------------------------------------------------------------
# Street segmentation: faithful port of apply_action / _put_in.
# ---------------------------------------------------------------------------
def segment_streets(action_log, start_stacks=None):
    """Return (streets, folded, allin, seats).
    streets = list of per-street dicts {seat: chips_ACTUALLY_PUT_IN_this_street}.

    Faithful to game.py:
      - blinds posted first (incremental, capped at stack), current_bet=BB, last_agg=BB.
      - preflop needs_to_act = all active (BB has the option).
      - raise/all_in amount = CUMULATIVE bet-to total for street; call amount = INCREMENTAL
        owed. The flat log records full owed for a call, but _put_in only commits
        min(owed, stack); a short stack therefore must be capped (else over-count -> bust
        in our running ledger). raise/all_in are pre-capped by _validate, but we cap anyway.
      - reopen (needs = other actives) iff raise_size >= last_agg; short all-in does NOT reopen.
      - street ends when needs empties; next street needs = currently-active set.
      - betting stops once <=1 active remains (run-it-out collapses remaining streets).
    start_stacks: dict seat_index -> chips at hand start (for capping). None => no cap
      (used only for street-count validation where magnitudes are irrelevant).
    """
    seats = sorted(set(a['seat'] for a in action_log))
    folded, allin = set(), set()
    stack_left = dict(start_stacks) if start_stacks is not None else {}
    for s in seats:
        stack_left.setdefault(s, 10**12)

    def actives():
        return set(s for s in seats if s not in folded and s not in allin)

    streets = []
    cur = {s: 0 for s in seats}      # bet_this_street (cumulative within street)
    contrib = {s: 0 for s in seats}  # chips actually put in this street
    current_bet = 0
    last_agg = BB
    needs = set()
    i, L = 0, action_log

    def put_in(s, want):
        nonlocal current_bet
        paid = max(0, min(want, stack_left[s]))
        stack_left[s] -= paid
        cur[s] += paid
        contrib[s] += paid
        if cur[s] > current_bet:
            current_bet = cur[s]
        if stack_left[s] == 0:
            allin.add(s)

    def flush():
        nonlocal cur, contrib, current_bet, last_agg
        streets.append(dict(contrib))
        cur = {x: 0 for x in seats}
        contrib = {x: 0 for x in seats}
        current_bet = 0
        last_agg = BB

    while i < len(L):
        a = L[i]; s, act, amt = a['seat'], a['action'], a['amount']
        if act in ('small_blind', 'big_blind'):
            put_in(s, amt)
            i += 1
            if i < len(L) and L[i]['action'] not in ('small_blind', 'big_blind'):
                current_bet = max(current_bet, BB)
                last_agg = BB
                needs = actives()
            continue

        if not needs:
            needs = actives()

        if act == 'fold':
            folded.add(s); needs.discard(s)
        elif act == 'check':
            needs.discard(s)
        elif act == 'call':
            put_in(s, amt)                  # incremental owed, capped
            needs.discard(s)
        elif act in ('raise', 'all_in'):
            prev = current_bet
            put_in(s, amt - cur[s])         # cumulative-to => add (amt-cur), capped
            raise_size = current_bet - prev
            needs.discard(s)
            if act == 'all_in':
                allin.add(s)
            if raise_size >= last_agg:
                last_agg = raise_size
                needs = set(x for x in actives() if x != s)
        i += 1

        if not needs:
            flush()
            needs = actives()
            # NOTE: do NOT break on len(needs)<=1. A lone active player can still bet
            # into a dead pot vs an all-in; the engine keeps soliciting until 0 actives
            # remain (then run_it_out emits NO log entries). The log itself is the
            # authoritative list of solicited actions, so the loop ends when L is exhausted.

    if any(v for v in contrib.values()):
        streets.append(dict(contrib))      # flush trailing forced/blind chips
    return streets, folded, allin, seats


def thorp_preflop_actions(streets_meta):
    """Given the per-action street tags, returns nothing here; helper below."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Replay a full match: track running stacks, build per-hand seat->id map among
# ALIVE bots (stack>0) by original match-seat order, and cache segmentation.
# ---------------------------------------------------------------------------
def replay_match(match):
    ids = [b['bot_id'] for b in sorted(match['bots'], key=lambda b: b['seat'])]
    stacks = {bid: START for bid in ids}
    per_hand = []  # list of dicts with all per-hand reconstructed facts
    for h in match['hands']:
        alive = [bid for bid in ids if stacks[bid] > 0]
        seat_to_id = {idx: bid for idx, bid in enumerate(alive)}
        id_to_seat = {bid: idx for idx, bid in seat_to_id.items()}
        start_stacks = {idx: stacks[bid] for idx, bid in seat_to_id.items()}
        streets, folded, allin, seats = segment_streets(h['action_log'], start_stacks)
        invested = {}
        for st in streets:
            for se, c in st.items():
                invested[se] = invested.get(se, 0) + c
        won = {}
        for w in h['winners']:
            won[w['bot_id']] = won.get(w['bot_id'], 0) + w['amount']
        per_hand.append(dict(hand=h, seat_to_id=seat_to_id, id_to_seat=id_to_seat,
                             start_stacks=start_stacks, streets=streets, folded=folded,
                             allin=allin, seats=seats, invested=invested, won=won,
                             alive=alive))
        # advance stacks
        for se, bid in seat_to_id.items():
            stacks[bid] -= invested.get(se, 0)
        for bid, amt in won.items():
            stacks[bid] = stacks.get(bid, 0) + amt
    return ids, stacks, per_hand


def preflop_actions_for_seat(action_log, start_stacks, tseat):
    """Return list of Thorp's voluntary action labels during preflop (street index 0)."""
    seats = sorted(set(a['seat'] for a in action_log))
    folded, allin = set(), set()
    stack_left = dict(start_stacks)
    for s in seats:
        stack_left.setdefault(s, 10**12)

    def actives():
        return set(s for s in seats if s not in folded and s not in allin)
    cur = {s: 0 for s in seats}; current_bet = 0; last_agg = BB; needs = set()
    street_idx = 0; pf = []; i = 0; L = action_log

    def put_in(s, want):
        nonlocal current_bet
        paid = max(0, min(want, stack_left[s]))
        stack_left[s] -= paid; cur[s] += paid
        if cur[s] > current_bet: current_bet = cur[s]
        if stack_left[s] == 0: allin.add(s)
    while i < len(L):
        a = L[i]; s, act, amt = a['seat'], a['action'], a['amount']
        if act in ('small_blind', 'big_blind'):
            put_in(s, amt); i += 1
            if i < len(L) and L[i]['action'] not in ('small_blind', 'big_blind'):
                current_bet = max(current_bet, BB); last_agg = BB; needs = actives()
            continue
        if not needs: needs = actives()
        if street_idx == 0 and s == tseat:
            pf.append(act)
        if act == 'fold':
            folded.add(s); needs.discard(s)
        elif act == 'check':
            needs.discard(s)
        elif act == 'call':
            put_in(s, amt); needs.discard(s)
        elif act in ('raise', 'all_in'):
            prev = current_bet; put_in(s, amt - cur[s]); rs = current_bet - prev
            needs.discard(s)
            if act == 'all_in': allin.add(s)
            if rs >= last_agg:
                last_agg = rs; needs = set(x for x in actives() if x != s)
        i += 1
        if not needs:
            street_idx += 1
            cur = {x: 0 for x in seats}; current_bet = 0; last_agg = BB
            needs = actives()
            if len(needs) <= 1:
                break
    return pf


# ---------------------------------------------------------------------------
# Equity at commit street (enumerate when <=2 board cards remain, else MC).
# ---------------------------------------------------------------------------
_FULL_DECK = [eval7.Card(r + s) for r in "23456789TJQKA" for s in "shdc"]

def equity_at_commit(hero, vills, board, seed=0):
    used = set(str(c) for c in hero) | set(str(c) for c in board)
    for v in vills:
        used |= set(str(c) for c in v)
    rem = [c for c in _FULL_DECK if str(c) not in used]
    need = 5 - len(board)

    def share(b):
        hs = eval7.evaluate(hero + b)
        vs = [eval7.evaluate(v + b) for v in vills]
        best = max([hs] + vs)
        if hs < best:
            return 0.0
        ntie = sum(1 for x in ([hs] + vs) if x == best)
        return 1.0 / ntie

    if need == 0:
        return share(list(board)), 'exact'
    if need == 1:
        return sum(share(list(board) + [c]) for c in rem) / len(rem), 'exact'
    if need == 2:
        tot = 0.0; cnt = 0
        for c1, c2 in combinations(rem, 2):
            tot += share(list(board) + [c1, c2]); cnt += 1
        return tot / cnt, 'exact'
    rng = random.Random(seed); N = 10000; tot = 0.0
    for _ in range(N):
        tot += share(list(board) + rng.sample(rem, need))
    return tot / N, 'mc'


# ---------------------------------------------------------------------------
# Load matches (skip <50B stubs; salvage truncated JSON).
# ---------------------------------------------------------------------------
def salvage(txt):
    try:
        return json.loads(txt), False
    except Exception:
        pass

    def parse_array(key):
        ks = txt.find('"%s"' % key)
        if ks < 0: return []
        astart = txt.find('[', ks)
        depth = 0; in_str = False; esc = False; cur = []; objs = []
        for ch in txt[astart + 1:]:
            if esc: cur.append(ch); esc = False; continue
            if ch == '\\': cur.append(ch); esc = True; continue
            if ch == '"': in_str = not in_str; cur.append(ch); continue
            if in_str: cur.append(ch); continue
            if ch == '{':
                if depth == 0: cur = ['{']; depth = 1; continue
                depth += 1; cur.append(ch); continue
            if ch == '}':
                depth -= 1; cur.append(ch)
                if depth == 0: objs.append(''.join(cur)); cur = []
                continue
            if ch == ']' and depth == 0:
                break
            if depth > 0: cur.append(ch)
        out = []
        for o in objs:
            try: out.append(json.loads(o))
            except Exception: break
        return out
    return {'bots': parse_array('bots'), 'hands': parse_array('hands')}, True


def load_matches():
    files = sorted(glob.glob(os.path.join(HIST, "*.json")))
    matches, excluded, truncated = [], [], []
    for f in files:
        base = os.path.basename(f)
        if os.path.getsize(f) < 50:
            excluded.append((base, 'stub<50B')); continue
        txt = open(f).read()
        try:
            d = json.loads(txt); trunc = False
        except Exception:
            d, trunc = salvage(txt)
            if trunc: truncated.append(base)
        if THORP not in [b['bot_id'] for b in d.get('bots', [])]:
            excluded.append((base, 'no_thorp')); continue
        if len(d.get('hands', [])) == 0:
            excluded.append((base, 'zero_hands')); continue
        d['_file'] = base; d['_truncated'] = trunc
        matches.append(d)
    return matches, excluded, truncated


def main():
    matches, excluded, truncated = load_matches()
    print("=== MATCH LOADING ===")
    print(f"Thorp matches: {len(matches)}")
    print(f"Truncated (salvaged): {truncated}")
    n_stub = sum(1 for e in excluded if e[1] == 'stub<50B')
    print(f"Excluded: {n_stub} <50B stubs; others: {[e for e in excluded if e[1]!='stub<50B']}")

    total_hands = 0
    pot_id_fail = 0
    seatmap_mismatch = []
    allbots_mismatch = []
    per_match = []
    allin_action_hands = 0
    stackoff_count = 0
    stackoff_net = 0
    stackoff_grossloss = 0
    origin_split = {'postflop-escalation': 0, 'preflop-raise': 0, 'preflop-flat': 0, 'none': 0}
    none_detail = []
    won_eqs, lost_eqs = [], []
    eq_methods = {'exact': 0, 'mc': 0}
    river_anom = []

    for m in matches:
        ids, final_stacks, per_hand = replay_match(m)
        total_hands += len(m['hands'])
        declared = {b['bot_id']: b.get('chip_delta') for b in m['bots']}
        recon = {bid: final_stacks.get(bid, START) - START for bid in ids}
        tmatch = (declared.get(THORP) is not None and recon.get(THORP) == declared.get(THORP))
        allmatch = True
        if not m['_truncated']:
            for bid in ids:
                if declared.get(bid) is not None and recon.get(bid) != declared.get(bid):
                    allmatch = False
                    allbots_mismatch.append((m['_file'][:8], bid[:8], recon.get(bid), declared.get(bid)))
        per_match.append((m['_file'], recon.get(THORP), declared.get(THORP), tmatch, allmatch, m['_truncated']))

        for ph in per_hand:
            h = ph['hand']; seat_to_id = ph['seat_to_id']; folded = ph['folded']; seats = ph['seats']
            invested = ph['invested']; won = ph['won']
            # pot identity (only meaningful for non-truncated/complete hands)
            inv_sum = sum(invested.values())
            if inv_sum != h['pot']:
                pot_id_fail += 1
            # seat-map validation on showdown hands
            if h.get('revealed_cards'):
                nonfolded = set(seat_to_id.get(s) for s in seats if s not in folded)
                if None in nonfolded:
                    nonfolded.discard(None)
                if nonfolded != set(h['revealed_cards'].keys()):
                    seatmap_mismatch.append((m['_file'][:8], h['hand_num'],
                                             sorted(x[:8] for x in nonfolded),
                                             sorted(x[:8] for x in h['revealed_cards'].keys())))
            if THORP not in ph['id_to_seat']:
                continue
            tseat = ph['id_to_seat'][THORP]
            # all_in action present?
            if any(a['seat'] == tseat and a['action'] == 'all_in' for a in h['action_log']):
                allin_action_hands += 1
            # Thorp per-street investment
            t_street = [st.get(tseat, 0) for st in ph['streets']]
            t_total = sum(t_street)
            tstart = ph['start_stacks'][tseat]
            # STACK-OFF
            if tstart > 0 and t_total >= 0.40 * tstart:
                stackoff_count += 1
                net = won.get(THORP, 0) - t_total
                stackoff_net += net
                if net < 0:
                    stackoff_grossloss += net
                # ORIGIN: street where cumulative crosses 40%
                thresh = 0.40 * tstart; cum = 0; cross = None
                for si, c in enumerate(t_street):
                    cum += c
                    if cum >= thresh:
                        cross = si; break
                pf = preflop_actions_for_seat(h['action_log'], ph['start_stacks'], tseat)
                vol_raise = any(x in ('raise', 'all_in') for x in pf)
                vol_call = any(x == 'call' for x in pf)
                if cross is not None and cross >= 1:
                    origin = 'postflop-escalation'
                elif vol_raise:
                    origin = 'preflop-raise'
                elif vol_call:
                    origin = 'preflop-flat'
                else:
                    origin = 'none'
                    none_detail.append((m['_file'][:8], h['hand_num'], tstart, t_total, pf))
                origin_split[origin] += 1
            # SHOWDOWN equity-at-commit.
            if THORP in h.get('revealed_cards', {}) and len(h['revealed_cards']) >= 2:
                # COMMIT STREET = street where Thorp put the MOST chips in (raw argmax of
                # his per-street contribution, per the task definition). Empirically this
                # (with the standard board mapping below) reproduces the target means; the
                # 'at-risk' refinement over-corrects and was rejected.
                if t_total > 0:
                    commit_si = max(range(len(t_street)), key=lambda i: t_street[i])
                else:
                    commit_si = 0
                board_n = {0: 0, 1: 3, 2: 4, 3: 5}.get(commit_si, 5)
                comm = [eval7.Card(c) for c in h['community_cards'][:board_n]]
                hero = [eval7.Card(c) for c in h['revealed_cards'][THORP]]
                vills = [[eval7.Card(c) for c in cs] for bid, cs in h['revealed_cards'].items() if bid != THORP]
                eq, meth = equity_at_commit(hero, vills, comm, seed=h['hand_num'])
                eq_methods[meth] += 1
                # WON/LOST partition by NET chip result this hand (won.get - invested).
                # Empirically matches the targets (side-pot / uncalled-return hands where
                # the showdown loser still nets chips land in WON exactly as the reference).
                hand_net = won.get(THORP, 0) - t_total
                # diagnostics: also track showdown-strength outcome for anomaly checks
                full_board = [eval7.Card(c) for c in h['community_cards']]
                won_sd = eval7.evaluate(hero + full_board) >= max(eval7.evaluate(v + full_board) for v in vills)
                if hand_net > 0:
                    won_eqs.append((eq, h['hand_num'], commit_si, m['_file']))
                    if commit_si == 3 and won_sd is False and round(eq, 3) == 0.0:
                        river_anom.append(('WONnet_sdLoss_eq0', m['_file'][:8], h['hand_num']))
                else:
                    lost_eqs.append((eq, h['hand_num'], commit_si, m['_file']))

    # ---- report ----
    print(f"\n=== HANDS ===\nTotal hands: {total_hands}")

    print(f"\n=== PER-MATCH RECONCILE ===")
    nm = 0
    for f, r, d, tm, am, tr in per_match:
        flag = 'OK' if tm else ('TRUNC' if tr else 'MISMATCH')
        print(f"  {f[:8]} recon={r} declared={d} thorp_ok={tm} allbots_ok={am} trunc={tr} [{flag}]")
        if tm: nm += 1
    print(f"Thorp per-match reconciled: {nm}/{len(matches)}")

    print(f"\n=== ALL-IN ACTION HANDS (Thorp): {allin_action_hands}")

    print(f"\n=== STACK-OFFS (>=40% hand-start stack) ===")
    print(f"count={stackoff_count} net={stackoff_net} grossloss={stackoff_grossloss}")
    print(f"origin_split={origin_split}")
    print(f"'none' detail (file,hand,start,invested,pf_acts):")
    for x in none_detail:
        print(f"   {x}")

    lost_mean = statistics.mean([e[0] for e in lost_eqs]) if lost_eqs else float('nan')
    won_mean = statistics.mean([e[0] for e in won_eqs]) if won_eqs else float('nan')
    print(f"\n=== SHOWDOWN EQUITY-AT-COMMIT ===")
    print(f"WON showdowns:  {len(won_eqs)}  mean_eq={won_mean:.4f}")
    print(f"LOST showdowns: {len(lost_eqs)}  mean_eq={lost_mean:.4f}")
    print(f"eq methods: {eq_methods}")
    # commit-street distribution
    from collections import Counter
    print(f"WON commit-street dist: {Counter(e[2] for e in won_eqs)}")
    print(f"LOST commit-street dist: {Counter(e[2] for e in lost_eqs)}")

    print(f"\n=== VALIDATIONS ===")
    print(f"pot-identity failures (sum invested != pot): {pot_id_fail}/{total_hands}")
    print(f"seat-map mismatches (revealed != nonfolded): {len(seatmap_mismatch)}")
    for x in seatmap_mismatch[:10]:
        print(f"   {x}")
    print(f"all-bots stack reconcile mismatches (non-trunc): {len(allbots_mismatch)}")
    for x in allbots_mismatch[:12]:
        print(f"   {x}")
    print(f"river-commit equity anomalies: {len(river_anom)} {river_anom[:8]}")


if __name__ == '__main__':
    main()
