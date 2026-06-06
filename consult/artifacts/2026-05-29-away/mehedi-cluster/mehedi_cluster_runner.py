#!/usr/bin/env python3
"""Lane-local Mehedi decision-cluster probe.

Writes only under consult/artifacts/2026-05-29-away/mehedi-cluster/.
Hero is always the locked submissions/v_final.zip artifact.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-away" / "mehedi-cluster"
SOURCE_HELPER_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-public-drift-patch"
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
HERO_ZIP = ROOT / "submissions" / "v_final.zip"
OPP_ZIP = LANE_DIR / "opponent_zips" / "mehedi_mybot.zip"
DECISION_LOG = LANE_DIR / "decision_log.jsonl"
RESULTS_JSON = LANE_DIR / "RESULTS.json"
STATUS_BLOCK = LANE_DIR / "STATUS_BLOCK.md"
REPORT_MD = LANE_DIR / "MEHEDI_CLUSTER_REPORT.md"

sys.path.insert(0, str(SOURCE_HELPER_DIR))
sys.path.insert(0, str(ENGINE_DIR))

import instrumented_h2h as helper  # noqa: E402
from engine.game import BIG_BLIND, STARTING_STACK  # noqa: E402
from sandbox import match as match_mod  # noqa: E402


BOOTSTRAP_ITERS = 5000
CI_ALPHA = 0.05
MATCH_RE = re.compile(r"_s(?P<base>\d+)_k(?P<k>\d+)_seed(?P<seed>\d+)_o(?P<orientation>\d+)$")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    idx = min(len(xs) - 1, max(0, math.ceil((p / 100.0) * len(xs)) - 1))
    return xs[idx]


def bb100(chips: int, hands: int) -> float:
    return 0.0 if hands <= 0 else (chips / BIG_BLIND) / (hands / 100.0)


def bootstrap_ci(samples: list[dict], seed: int = 20260529) -> dict:
    if not samples:
        return {"mean": 0.0, "low": 0.0, "high": 0.0, "half_width": 0.0}
    rng = random.Random(seed)
    n = len(samples)
    draws = []
    for _ in range(BOOTSTRAP_ITERS):
        chips = 0
        scheduled = 0
        for _ in range(n):
            s = samples[rng.randrange(n)]
            chips += int(s["chip_delta"])
            scheduled += int(s["scheduled_hands"])
        draws.append(bb100(chips, scheduled))
    draws.sort()
    total_chips = sum(int(s["chip_delta"]) for s in samples)
    total_scheduled = sum(int(s["scheduled_hands"]) for s in samples)
    low = draws[int(BOOTSTRAP_ITERS * CI_ALPHA / 2)]
    high = draws[int(BOOTSTRAP_ITERS * (1 - CI_ALPHA / 2))]
    return {
        "mean": bb100(total_chips, total_scheduled),
        "low": low,
        "high": high,
        "half_width": (high - low) / 2.0,
    }


def parse_match_id(hand_id: str | None) -> str:
    if not hand_id or "_h" not in hand_id:
        return "unknown"
    return hand_id.rsplit("_h", 1)[0]


def parse_match_schedule(match_id: str) -> dict:
    m = MATCH_RE.search(match_id)
    if not m:
        return {"base": None, "seed": None, "orientation": None}
    return {
        "base": int(m.group("base")),
        "seed": int(m.group("seed")),
        "orientation": int(m.group("orientation")),
    }


def action_class(action: dict, state: dict) -> str:
    act = str(action.get("action") or "unknown")
    bucket = helper.sizing_bucket(action, state)
    return act if bucket == act else f"{act} / {bucket}"


def extract_raw_action(action: dict | None) -> dict:
    if not isinstance(action, dict):
        return {"action": "fold", "error": "missing_action"}
    out = {"action": action.get("action")}
    if "amount" in action:
        out["amount"] = action.get("amount")
    if "error" in action:
        out["error"] = action.get("error")
    return out


class DecisionLoggingBotProcess(match_mod.BotProcess):
    records: list[dict] = []
    latencies = defaultdict(list)
    stdout_noise = defaultdict(int)
    stdout_noise_examples = defaultdict(list)

    @classmethod
    def reset(cls) -> None:
        cls.records = []
        cls.latencies = defaultdict(list)
        cls.stdout_noise = defaultdict(int)
        cls.stdout_noise_examples = defaultdict(list)

    def _read_json_obj(self) -> dict:
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise EOFError("Bot process died")
            text = line.strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                self.stdout_noise[self.bot_id] += 1
                if len(self.stdout_noise_examples[self.bot_id]) < 5:
                    self.stdout_noise_examples[self.bot_id].append(text[:200])

    def warmup(self) -> None:
        if self._proc is None:
            return
        try:
            self._proc.stdin.write(json.dumps({"type": "warmup"}) + "\n")
            self._proc.stdin.flush()
            self._read_json_obj()
        except Exception as e:
            self.errors.append("warmup_failed: " + str(e))

    def act(self, game_state: dict) -> dict:
        if self._proc is None:
            return {"action": "fold", "error": "no_process"}
        start = time.perf_counter()
        action = None
        try:
            self._proc.stdin.write(json.dumps(game_state) + "\n")
            self._proc.stdin.flush()
            action = self._read_json_obj()
            if "error" in action:
                self.errors.append(action["error"])
            return action
        except Exception as e:
            self.errors.append(str(e))
            action = {"action": "fold", "error": str(e)}
            return action
        finally:
            elapsed = time.perf_counter() - start
            self.latencies[self.bot_id].append(elapsed)
            if self.bot_id != "hero" or game_state.get("type") != "action_request" or action is None:
                pass
            else:
                hand_id = game_state.get("hand_id")
                match_id = parse_match_id(hand_id)
                sched = parse_match_schedule(match_id)
                board = list(game_state.get("community_cards", []))
                raw = extract_raw_action(action)
                self.records.append({
                    "hand_id": hand_id,
                    "match_id": match_id,
                    "base": sched["base"],
                    "seed": sched["seed"],
                    "orientation": sched["orientation"],
                    "street": game_state.get("street"),
                    "seat_to_act": game_state.get("seat_to_act"),
                    "position_label": helper.position_label_shipped(game_state),
                    "true_position_label": helper.position_label_trueish(game_state),
                    "action": raw.get("action"),
                    "amount": raw.get("amount"),
                    "raw_action": raw,
                    "action_class": action_class(raw, game_state),
                    "sizing_bucket": helper.sizing_bucket(raw, game_state),
                    "pot": game_state.get("pot"),
                    "amount_owed": game_state.get("amount_owed"),
                    "can_check": game_state.get("can_check"),
                    "current_bet": game_state.get("current_bet"),
                    "min_raise_to": game_state.get("min_raise_to"),
                    "board": board,
                    "board_texture_bucket": helper.board_texture_tag(board),
                    "hero_cards": game_state.get("your_cards"),
                    "your_stack": game_state.get("your_stack"),
                    "your_bet_this_street": game_state.get("your_bet_this_street"),
                    "preflop_raise_count": helper.current_preflop_raise_count(game_state),
                    "facing_raise": helper.facing_raise(game_state),
                    "action_log_len": len(game_state.get("action_log", [])),
                    "decision_latency_s": elapsed,
                })


def cluster_key(rec: dict) -> tuple:
    return (
        rec.get("street"),
        rec.get("position_label"),
        rec.get("action_class"),
        rec.get("board_texture_bucket"),
    )


def empty_bucket(mode: str) -> dict:
    return {"mode": mode, "chips": 0, "n_decisions": 0, "hands": set(), "examples": []}


def render_buckets(buckets: dict, scheduled: int) -> list[dict]:
    rows = []
    for key, b in buckets.items():
        chips = int(b["chips"])
        rows.append({
            "mode": b["mode"],
            "street": key[0],
            "position": key[1],
            "action": key[2],
            "board_texture": key[3],
            "chips": chips,
            "scheduled_bb_per_100": bb100(chips, scheduled),
            "n_hands": len(b["hands"]),
            "n_decisions": int(b["n_decisions"]),
            "examples": b["examples"],
        })
    rows.sort(key=lambda r: r["scheduled_bb_per_100"])
    return rows


def summarize_records(records: list[dict], scheduled: int) -> dict:
    by_hand = defaultdict(list)
    for rec in records:
        by_hand[rec["hand_id"]].append(rec)

    last = defaultdict(lambda: empty_bucket("last_decision_losing_hands"))
    every = defaultdict(lambda: empty_bucket("every_decision_losing_hands"))
    street = defaultdict(lambda: {"chips": 0, "n_hands": 0})
    texture = defaultdict(lambda: {"chips": 0, "n_hands": 0})
    antecedent = defaultdict(lambda: {"chips": 0, "n_hands": 0, "n_opens": 0, "examples": []})

    for hand_id, recs in by_hand.items():
        delta = int(recs[-1].get("final_hand_chip_delta", 0))
        if delta >= 0:
            continue
        last_rec = recs[-1]
        k = cluster_key(last_rec)
        b = last[k]
        b["chips"] += delta
        b["n_decisions"] += 1
        b["hands"].add(hand_id)
        if len(b["examples"]) < 5:
            b["examples"].append({
                "hand_id": hand_id,
                "match_id": last_rec.get("match_id"),
                "seed": last_rec.get("seed"),
                "orientation": last_rec.get("orientation"),
                "hero_cards": last_rec.get("hero_cards"),
                "board": last_rec.get("board"),
                "final_board": last_rec.get("final_board"),
                "pot": last_rec.get("pot"),
                "amount_owed": last_rec.get("amount_owed"),
                "delta": delta,
            })
        street[last_rec.get("street")]["chips"] += delta
        street[last_rec.get("street")]["n_hands"] += 1
        texture[last_rec.get("board_texture_bucket")]["chips"] += delta
        texture[last_rec.get("board_texture_bucket")]["n_hands"] += 1

        for rec in recs:
            k2 = cluster_key(rec)
            b2 = every[k2]
            b2["chips"] += delta
            b2["n_decisions"] += 1
            b2["hands"].add(hand_id)
            if len(b2["examples"]) < 3:
                b2["examples"].append({
                    "hand_id": hand_id,
                    "match_id": rec.get("match_id"),
                    "seed": rec.get("seed"),
                    "orientation": rec.get("orientation"),
                    "hero_cards": rec.get("hero_cards"),
                    "board": rec.get("board"),
                    "final_board": rec.get("final_board"),
                    "pot": rec.get("pot"),
                    "amount_owed": rec.get("amount_owed"),
                    "delta": delta,
                })

        has_river_decision = any(r.get("street") == "river" for r in recs)
        if has_river_decision:
            for rec in recs:
                if rec.get("street") != "preflop" or rec.get("action") != "raise":
                    continue
                if int(rec.get("preflop_raise_count") or 0) != 0:
                    continue
                ak = (
                    rec.get("position_label"),
                    rec.get("true_position_label"),
                    rec.get("action_class"),
                )
                a = antecedent[ak]
                a["chips"] += delta
                a["n_hands"] += 1
                a["n_opens"] += 1
                if len(a["examples"]) < 5:
                    a["examples"].append({
                        "hand_id": hand_id,
                        "match_id": rec.get("match_id"),
                        "seed": rec.get("seed"),
                        "orientation": rec.get("orientation"),
                        "hero_cards": rec.get("hero_cards"),
                        "delta": delta,
                    })

    street_rows = [
        {
            "street": key,
            "chips": int(data["chips"]),
            "scheduled_bb_per_100": bb100(int(data["chips"]), scheduled),
            "n_hands": int(data["n_hands"]),
        }
        for key, data in street.items()
    ]
    street_rows.sort(key=lambda r: r["scheduled_bb_per_100"])

    texture_rows = [
        {
            "board_texture": key,
            "chips": int(data["chips"]),
            "scheduled_bb_per_100": bb100(int(data["chips"]), scheduled),
            "n_hands": int(data["n_hands"]),
        }
        for key, data in texture.items()
    ]
    texture_rows.sort(key=lambda r: r["scheduled_bb_per_100"])

    antecedent_rows = [
        {
            "position": key[0],
            "true_position": key[1],
            "action": key[2],
            "chips": int(data["chips"]),
            "scheduled_bb_per_100": bb100(int(data["chips"]), scheduled),
            "n_hands": int(data["n_hands"]),
            "n_opens": int(data["n_opens"]),
            "examples": data["examples"],
        }
        for key, data in antecedent.items()
    ]
    antecedent_rows.sort(key=lambda r: r["scheduled_bb_per_100"])

    last_rows = render_buckets(last, scheduled)
    every_rows = render_buckets(every, scheduled)
    top_rows = sorted(last_rows[:10] + every_rows[:10], key=lambda r: r["scheduled_bb_per_100"])[:10]
    return {
        "last_decision_losing_hands": last_rows,
        "every_decision_losing_hands": every_rows,
        "street_only_last_decision_losing_hands": street_rows,
        "board_texture_last_decision_losing_hands": texture_rows,
        "top_10_clusters_by_scheduled_impact": top_rows,
        "antecedent_preflop_opens_before_river_losses": antecedent_rows,
    }


def to_markdown_table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(out)


def fmt(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:+.{digits}f}" if value < 0 or value > 0 else f"{value:.{digits}f}"


def classify_toby_overlap(row: dict) -> tuple[str, str]:
    street = row.get("street")
    action = str(row.get("action"))
    texture = str(row.get("board_texture"))
    position = str(row.get("position"))
    if street == "river" and "raise" in action and texture == "5card_unpaired_two_tone_static" and position == "heads_up_button":
        return "river raise / unpaired two-tone static", "same"
    if street == "river" and "fold" in action and texture == "5card_paired_two_tone_static":
        return "river fold / paired two-tone static", "same"
    return "no Toby top-cluster match", "different"


def choose_verdict(clusters: dict, summary: dict) -> tuple[str, str]:
    actual = int(summary["actual_hands"])
    ci = summary["ci"]
    if actual < 1000 or not clusters["last_decision_losing_hands"]:
        return "INCONCLUSIVE", "insufficient actual hands or decision logs"
    top3 = clusters["last_decision_losing_hands"][:3]
    top2 = clusters["last_decision_losing_hands"][:2]
    if any(row.get("street") == "preflop" for row in top2):
        same_impact = 0.0
        for row in clusters["last_decision_losing_hands"][:10]:
            _, same = classify_toby_overlap(row)
            if same == "same":
                same_impact += float(row["scheduled_bb_per_100"])
        top2_impact = sum(float(row["scheduled_bb_per_100"]) for row in top2)
        return (
            "DIFFERENT_LEAK",
            "dominant top-2 last-decision clusters are preflop "
            f"({top2_impact:+.2f} scheduled bb/100); Toby-style river clusters are present but secondary "
            f"({same_impact:+.2f} scheduled bb/100 in top-10 last clusters)",
        )
    same_rows = []
    for row in top3:
        _, same = classify_toby_overlap(row)
        if same == "same" and abs(float(row["scheduled_bb_per_100"])) >= 0.5:
            same_rows.append(row)
    if same_rows:
        impact = sum(float(r["scheduled_bb_per_100"]) for r in same_rows)
        return "SAME_TRAP", f"top-3 last-decision clusters overlap Toby river trap pattern for {impact:+.2f} scheduled bb/100"
    if ci["high"] - ci["low"] > 20 and summary["scheduled_bb_per_100"] < 0:
        return "INCONCLUSIVE", "loss is negative but localization CI is wide"
    return "DIFFERENT_LEAK", "top last-decision clusters do not overlap Toby river paired/unpaired trap pattern"


def write_reports(result: dict) -> None:
    clusters = result["clusters"]
    verdict, reason = choose_verdict(clusters, result["h2h_summary"])
    result["verdict"] = verdict
    result["verdict_reason"] = reason
    ship_recommendation = "SHIP_LOCKED_ARTIFACT"
    result["ship_recommendation"] = ship_recommendation

    top = clusters["last_decision_losing_hands"][:10]
    top_rows = []
    for i, row in enumerate(top, start=1):
        note, same = classify_toby_overlap(row)
        top_rows.append([
            i,
            row["mode"],
            row["street"],
            row["position"],
            row["action"],
            row["board_texture"],
            row["chips"],
            fmt(row["scheduled_bb_per_100"]),
            row["n_hands"],
            row["n_decisions"],
            f"{same}: {note}",
        ])

    toby_patterns = [
        ("river heads_up_button raise / raise_le_2/3pot on unpaired two-tone static wet-flush-draw boards", "river raise / unpaired two-tone static"),
        ("river fold on paired two-tone static boards", "river fold / paired two-tone static"),
        ("same paired-board fold cluster with label drift", "river fold / paired two-tone static"),
        ("preflop HU button open-any antecedent, not primary kill", "preflop open antecedent"),
    ]
    comparison_rows = []
    for label, needle in toby_patterns:
        matches = []
        if needle == "preflop open antecedent":
            for row in clusters["antecedent_preflop_opens_before_river_losses"][:5]:
                if row["position"] == "heads_up_button":
                    matches.append(f"{row['position']} {row['action']} {fmt(row['scheduled_bb_per_100'])} bb/100")
        else:
            for row in clusters["last_decision_losing_hands"][:10]:
                note, same = classify_toby_overlap(row)
                if same == "same" and note == needle:
                    matches.append(f"{row['street']} {row['position']} {row['action']} {row['board_texture']} {fmt(row['scheduled_bb_per_100'])} bb/100")
        comparison_rows.append([
            label,
            "<br>".join(matches) if matches else "none in top last-decision clusters",
            "same" if matches and needle != "preflop open antecedent" else ("antecedent only" if matches else "different"),
            reason if matches else "Top Mehedi clusters are outside this Toby pattern.",
        ])

    h = result["h2h_summary"]
    h2h_table = to_markdown_table(
        ["scheduled hands", "actual hands", "scheduled bb/100", "actual bb/100", "95% CI", "hero errors", "opponent errors", "p99 latency"],
        [[
            h["scheduled_hands"],
            h["actual_hands"],
            fmt(h["scheduled_bb_per_100"]),
            fmt(h["actual_bb_per_100"]),
            f"[{fmt(h['ci']['low'])}, {fmt(h['ci']['high'])}]",
            h["hero_errors"],
            h["opponent_errors"],
            f"{h['hero_p99_latency_s']:.4f}s" if h["hero_p99_latency_s"] is not None else "n/a",
        ]],
    )
    top_table = to_markdown_table(
        ["rank", "attribution mode", "street", "position", "action", "board texture", "chips", "scheduled bb/100", "n hands", "n decisions", "notes"],
        top_rows,
    )
    comparison_table = to_markdown_table(
        ["Toby cluster", "Mehedi matching cluster", "same/different", "evidence"],
        comparison_rows,
    )

    report = "\n".join([
        verdict,
        "",
        "# Mehedi decision-cluster report",
        "",
        f"Verdict reason: {reason}.",
        "",
        "## H2H summary",
        "",
        h2h_table,
        "",
        "## Top cluster table",
        "",
        top_table,
        "",
        "## Toby comparison",
        "",
        comparison_table,
        "",
        "## Ship recommendation",
        "",
        ship_recommendation,
        "",
        "Do not replace `submissions/v_final.zip` or `submissions/best_green.zip`; no candidate artifact was built.",
        "",
    ])
    REPORT_MD.write_text(report, encoding="utf-8")

    status = "\n".join([
        "MEHEDI_CLUSTER_STATUS",
        f"- verdict: {verdict}",
        f"- scheduled_hands: {h['scheduled_hands']}",
        f"- actual_hands: {h['actual_hands']}",
        f"- scheduled_bb_per_100: {h['scheduled_bb_per_100']:+.2f}",
        f"- actual_bb_per_100: {h['actual_bb_per_100']:+.2f}",
        f"- ci_95: [{h['ci']['low']:+.2f}, {h['ci']['high']:+.2f}]",
        f"- hero_errors: {h['hero_errors']}",
        f"- opponent_errors: {h['opponent_errors']}",
        f"- p99_latency_s: {h['hero_p99_latency_s'] if h['hero_p99_latency_s'] is not None else 'n/a'}",
        f"- protected_sha_before: {result['protected_sha_before']}",
        f"- protected_sha_after: {result.get('protected_sha_after', 'pending')}",
        "- recommendation: SHIP_LOCKED_ARTIFACT",
        "",
    ])
    STATUS_BLOCK.write_text(status, encoding="utf-8")


def run(args: argparse.Namespace) -> dict:
    LANE_DIR.mkdir(parents=True, exist_ok=True)
    samples = []
    match_rows = []
    hand_meta = {}
    scheduled_total = 0
    actual_total = 0
    hero_errors = 0
    opponent_errors = 0

    original_bot_process = match_mod.BotProcess
    match_mod.BotProcess = DecisionLoggingBotProcess
    DecisionLoggingBotProcess.reset()

    try:
        for base in args.bases:
            k = 0
            base_scheduled = 0
            while base_scheduled < args.hands_per_base:
                seed = base + k * args.seed_stride
                pair_chip_delta = 0
                pair_actual = 0
                for orientation, paths in enumerate([
                    {"hero": str(HERO_ZIP.resolve()), "opp": str(OPP_ZIP.resolve())},
                    {"opp": str(OPP_ZIP.resolve()), "hero": str(HERO_ZIP.resolve())},
                ]):
                    match_id = f"mehedi_cluster_s{base}_k{k}_seed{seed}_o{orientation}"
                    row = {
                        "base": base,
                        "seed": seed,
                        "orientation": orientation,
                        "match_id": match_id,
                        "attempted_hands": args.match_len,
                    }
                    try:
                        result = match_mod.run_match(match_id, paths, n_hands=args.match_len, verbose=False, seed=seed)
                        row.update({
                            "hands": int(result["n_hands"]),
                            "duration_s": float(result["duration_s"]),
                            "hero_chip_delta": int(result["chip_delta"]["hero"]),
                            "opp_chip_delta": int(result["chip_delta"]["opp"]),
                            "hero_errors": list(result["bot_errors"]["hero"]),
                            "opp_errors": list(result["bot_errors"]["opp"]),
                        })
                        prev_hero_stack = STARTING_STACK
                        for hand in result.get("hands", []):
                            final_hero_stack = int(hand.get("final_stacks", {}).get("hero", prev_hero_stack))
                            hid = hand.get("hand_id")
                            hand_meta[hid] = {
                                "final_hand_chip_delta": final_hero_stack - prev_hero_stack,
                                "final_board": list(hand.get("community_cards", [])),
                                "final_street": hand.get("street"),
                                "showdown": bool(hand.get("showdown")),
                            }
                            prev_hero_stack = final_hero_stack
                    except Exception as e:
                        row.update({
                            "hands": 0,
                            "duration_s": 0.0,
                            "hero_chip_delta": 0,
                            "opp_chip_delta": 0,
                            "hero_errors": [f"match_failed: {e}"],
                            "opp_errors": [],
                        })
                    match_rows.append(row)
                    scheduled_total += args.match_len
                    base_scheduled += args.match_len
                    actual_total += int(row["hands"])
                    pair_actual += int(row["hands"])
                    pair_chip_delta += int(row["hero_chip_delta"])
                    hero_errors += len(row["hero_errors"])
                    opponent_errors += len(row["opp_errors"])
                samples.append({
                    "base": base,
                    "seed": seed,
                    "scheduled_hands": 2 * args.match_len,
                    "actual_hands": pair_actual,
                    "chip_delta": pair_chip_delta,
                    "scheduled_bb_per_100": bb100(pair_chip_delta, 2 * args.match_len),
                })
                print(
                    f"[mehedi] base={base} seed={seed} scheduled={scheduled_total} actual={actual_total} "
                    f"bb100={bb100(sum(s['chip_delta'] for s in samples), scheduled_total):+.2f}",
                    flush=True,
                )
                k += 1
    finally:
        match_mod.BotProcess = original_bot_process

    records = DecisionLoggingBotProcess.records
    by_hand = defaultdict(list)
    for rec in records:
        meta = hand_meta.get(rec["hand_id"], {})
        rec["final_hand_chip_delta"] = int(meta.get("final_hand_chip_delta", 0))
        rec["final_board"] = meta.get("final_board", [])
        rec["final_board_texture_bucket"] = helper.board_texture_tag(rec["final_board"])
        rec["final_street"] = meta.get("final_street")
        rec["showdown"] = meta.get("showdown")
        by_hand[rec["hand_id"]].append(rec)

    for recs in by_hand.values():
        for rec in recs:
            rec["is_last_hero_decision_in_hand"] = False
        recs[-1]["is_last_hero_decision_in_hand"] = True

    with DECISION_LOG.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    ci = bootstrap_ci(samples)
    hero_latencies = DecisionLoggingBotProcess.latencies.get("hero", [])
    h2h_summary = {
        "scheduled_hands": scheduled_total,
        "actual_hands": actual_total,
        "scheduled_bb_per_100": bb100(sum(s["chip_delta"] for s in samples), scheduled_total),
        "actual_bb_per_100": bb100(sum(s["chip_delta"] for s in samples), actual_total),
        "ci": ci,
        "hero_errors": hero_errors,
        "opponent_errors": opponent_errors,
        "hero_p99_latency_s": percentile(hero_latencies, 99),
        "hero_max_latency_s": max(hero_latencies) if hero_latencies else None,
    }
    result = {
        "created_at": now_iso(),
        "lane_dir": str(LANE_DIR),
        "hero_zip_info": helper.describe_zip(HERO_ZIP),
        "opponent_zip_info": helper.describe_zip(OPP_ZIP),
        "opponent_repo": "Mehedi-dev-2404/fullhouse-engine",
        "opponent_head_sha": "aa14a35a4f185f8608ae962aef17a7c620909a4b",
        "opponent_bot_path": "bots/mybot/bot.py",
        "bases": args.bases,
        "hands_per_base": args.hands_per_base,
        "match_len": args.match_len,
        "seed_stride": args.seed_stride,
        "h2h_summary": h2h_summary,
        "samples": samples,
        "match_rows": match_rows,
        "decision_count": len(records),
        "clusters": summarize_records(records, scheduled_total),
        "paths": {
            "decision_log": str(DECISION_LOG),
            "results_json": str(RESULTS_JSON),
            "report": str(REPORT_MD),
            "status_block": str(STATUS_BLOCK),
        },
        "protected_sha_before": (LANE_DIR / "protected_sha_before.txt").read_text(encoding="utf-8").strip(),
    }
    write_reports(result)
    RESULTS_JSON.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bases", type=int, nargs="+", default=[142])
    parser.add_argument("--hands-per-base", type=int, default=20000)
    parser.add_argument("--match-len", type=int, default=500)
    parser.add_argument("--seed-stride", type=int, default=1000)
    args = parser.parse_args()
    result = run(args)
    h = result["h2h_summary"]
    print(json.dumps({
        "scheduled_hands": h["scheduled_hands"],
        "actual_hands": h["actual_hands"],
        "scheduled_bb_per_100": h["scheduled_bb_per_100"],
        "actual_bb_per_100": h["actual_bb_per_100"],
        "ci": h["ci"],
        "decision_count": result["decision_count"],
        "verdict": result.get("verdict"),
        "paths": result["paths"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
