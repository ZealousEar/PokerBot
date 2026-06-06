#!/usr/bin/env python3
"""Artifact-local decision-cluster probe for Mehedi public-drift analysis.

Writes only under consult/artifacts/2026-05-29-mehedi-cluster/.
Does not edit ext/, submissions/, src/, data/, tools/, tests/, or opponent sources.
Reuses the prebuilt Mehedi opponent zip from the public-repo-drift artifact.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
ARTIFACT_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-mehedi-cluster"
LOG_DIR = ARTIFACT_DIR / "logs"
HERO_ZIP = ROOT / "submissions" / "v_final.zip"
DEFAULT_OPP_ZIP = ROOT / "consult" / "artifacts" / "2026-05-29-public-repo-drift" / "opponent_zips" / "mehedi_mybot.zip"

sys.path.insert(0, str(ENGINE_DIR))
from engine.game import BIG_BLIND, STARTING_STACK  # noqa: E402
from sandbox import match as match_mod  # noqa: E402

RANK_ORDER = {r: i for i, r in enumerate("23456789TJQKA", start=2)}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def describe_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        names = sorted(z.namelist())
        infos = z.infolist()
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "has_root_bot_py": "bot.py" in names,
        "data_bytes": sum(i.file_size for i in infos if i.filename.startswith("data/")),
        "sha256": sha256(path),
    }


def ensure_root_bot_zip(src_dir: Path, out_zip: Path) -> dict:
    src_dir = src_dir.resolve()
    if not (src_dir / "bot.py").is_file():
        raise FileNotFoundError(f"missing bot.py under {src_dir}")
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(src_dir / "bot.py", "bot.py")
        data_dir = src_dir / "data"
        if data_dir.is_dir():
            for f in sorted(data_dir.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts and not f.name.endswith((".pyc", ".pyo")):
                    z.write(f, str(Path("data") / f.relative_to(data_dir)))
    return describe_zip(out_zip)


def bb100(chips: int, hands: int) -> float:
    return 0.0 if hands <= 0 else (chips / BIG_BLIND) / (hands / 100.0)


def mbb_per_game(chips: int, games: int) -> float:
    return 0.0 if games <= 0 else (chips / BIG_BLIND) / games * 1000.0


def position_label_shipped(state: dict) -> str:
    players = state.get("players") or []
    seat = int(state.get("seat_to_act", 0))
    if len(players) <= 2:
        if state.get("street") == "preflop":
            voluntary = [a for a in state.get("action_log", []) if a.get("action") not in ("small_blind", "big_blind")]
            if not voluntary and not state.get("can_check", False):
                return "heads_up_button"
            return "big_blind"
        return "heads_up_button" if seat == 0 else "big_blind"
    if seat >= len(players) - 2:
        return "button"
    if seat <= 1:
        return "early"
    return "middle"


def blind_seats(state: dict) -> tuple[int | None, int | None]:
    sb = bb = None
    for a in state.get("action_log", []):
        if a.get("action") == "small_blind" and sb is None:
            sb = int(a.get("seat", -1))
        elif a.get("action") == "big_blind" and bb is None:
            bb = int(a.get("seat", -1))
        if sb is not None and bb is not None:
            break
    return sb, bb


def position_label_trueish(state: dict) -> str:
    players = state.get("players") or []
    n = len(players)
    seat = int(state.get("seat_to_act", 0))
    sb, bb = blind_seats(state)
    if n <= 2:
        if seat == sb:
            return "heads_up_button"
        if seat == bb:
            return "big_blind"
        return position_label_shipped(state)
    if sb is None or bb is None:
        return "unknown"
    button = (sb - 1) % n
    if seat == button:
        return "button"
    if seat == sb:
        return "small_blind"
    if seat == bb:
        return "big_blind"
    order = []
    s = (bb + 1) % n
    while s != button:
        order.append(s)
        s = (s + 1) % n
    if seat in order[:2]:
        return "early"
    return "middle"


def board_texture_tag(board: list[str]) -> str:
    if not board:
        return "preflop"
    ranks = [c[0] for c in board]
    suits = [c[1] for c in board if len(c) > 1]
    counts = Counter(ranks)
    pair_tag = "paired" if max(counts.values()) >= 2 else "unpaired"
    suit_counts = Counter(suits)
    if suit_counts and max(suit_counts.values()) == len(suits):
        suit_tag = "monotone"
    elif suit_counts and max(suit_counts.values()) >= 2:
        suit_tag = "two_tone"
    else:
        suit_tag = "rainbow"
    vals = sorted(RANK_ORDER.get(r, 0) for r in ranks)
    connected = len(vals) >= 3 and vals[-1] - vals[0] <= 5
    return f"{len(board)}card_{pair_tag}_{suit_tag}_{'connected' if connected else 'static'}"


def sizing_bucket(action: dict, state: dict) -> str:
    a = action.get("action")
    if a in ("fold", "check", "all_in"):
        return str(a)
    pot = max(1, int(state.get("pot", 0)))
    owed = int(state.get("amount_owed", 0))
    if a == "call":
        if owed >= int(state.get("your_stack", 0)):
            return "call_allin"
        frac = owed / pot
        if frac <= 0.34:
            return "call_le_1/3pot"
        if frac <= 0.75:
            return "call_le_3/4pot"
        return "call_big"
    if a == "raise":
        amount = int(action.get("amount") or 0)
        if amount >= int(state.get("your_stack", 0)) + int(state.get("your_bet_this_street", 0)):
            return "raise_stack"
        if amount <= int(state.get("min_raise_to", 0)):
            return "raise_min"
        frac = (amount - int(state.get("your_bet_this_street", 0))) / pot
        if frac <= 0.40:
            return "raise_le_1/3pot"
        if frac <= 0.80:
            return "raise_le_2/3pot"
        if frac <= 1.20:
            return "raise_pot"
        return "raise_overpot"
    return str(a or "unknown")


def current_preflop_raise_count(state: dict) -> int:
    if state.get("street") != "preflop":
        return 0
    return sum(1 for a in state.get("action_log", []) if a.get("action") in ("raise", "all_in"))


def facing_raise(state: dict) -> bool:
    return int(state.get("amount_owed", 0)) > 0


class LoggingBotProcess(match_mod.BotProcess):
    records: list[dict] = []
    latencies = defaultdict(list)
    stdout_noise = defaultdict(int)
    stdout_noise_examples = defaultdict(list)

    @classmethod
    def reset(cls):
        cls.records = []
        cls.latencies = defaultdict(list)
        cls.stdout_noise = defaultdict(int)
        cls.stdout_noise_examples = defaultdict(list)

    def _read_json_obj(self):
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

    def warmup(self):
        if self._proc is None:
            return
        try:
            self._proc.stdin.write(json.dumps({"type": "warmup"}) + "\n")
            self._proc.stdin.flush()
            self._read_json_obj()
        except Exception as e:
            self.errors.append("warmup_failed: " + str(e))

    def act(self, game_state):
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
            if self.bot_id == "hero" and game_state.get("type") == "action_request" and action is not None:
                board = list(game_state.get("community_cards", []))
                rec = {
                    "bot_id": self.bot_id,
                    "hand_id": game_state.get("hand_id"),
                    "street": game_state.get("street"),
                    "seat_to_act": game_state.get("seat_to_act"),
                    "position_label": position_label_shipped(game_state),
                    "true_position_label": position_label_trueish(game_state),
                    "action": action.get("action"),
                    "amount": action.get("amount"),
                    "action_class": sizing_bucket(action, game_state),
                    "sizing_bucket": sizing_bucket(action, game_state),
                    "board_texture": board_texture_tag(board),
                    "board_texture_tag": board_texture_tag(board),
                    "raw_action": action,
                    "pot": game_state.get("pot"),
                    "amount_owed": game_state.get("amount_owed"),
                    "can_check": game_state.get("can_check"),
                    "your_stack": game_state.get("your_stack"),
                    "your_bet_this_street": game_state.get("your_bet_this_street"),
                    "current_bet": game_state.get("current_bet"),
                    "min_raise_to": game_state.get("min_raise_to"),
                    "your_cards": game_state.get("your_cards"),
                    "preflop_raise_count": current_preflop_raise_count(game_state),
                    "facing_raise": facing_raise(game_state),
                    "action_log_len": len(game_state.get("action_log", [])),
                    "decision_latency_s": elapsed,
                }
                self.records.append(rec)


def run_probe(name: str, opp_zip: Path, repo: str, head_sha: str, bot_path: str,
              base: int, target_hands: int, match_len: int, seed_stride: int) -> dict:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    opp_zip = opp_zip.resolve()
    opp_zip_info = describe_zip(opp_zip)
    hero_info = describe_zip(HERO_ZIP)

    decisions_path = ARTIFACT_DIR / "decision_log.jsonl"
    match_json_path = LOG_DIR / f"{name}_instrumented_s{base}.json"
    summary_path = LOG_DIR / f"{name}_clusters_s{base}.json"

    original_bot_process = match_mod.BotProcess
    match_mod.BotProcess = LoggingBotProcess
    LoggingBotProcess.reset()

    samples = []
    match_rows = []
    per_hand_delta = {}
    attempted_total = 0
    hands_total = 0
    match_count = 0
    hero_errors = 0
    opp_errors = 0

    try:
        k = 0
        while attempted_total < target_hands:
            seed = base + k * seed_stride
            for orientation, paths in enumerate([
                {"hero": str(HERO_ZIP.resolve()), "opp": str(opp_zip.resolve())},
                {"opp": str(opp_zip.resolve()), "hero": str(HERO_ZIP.resolve())},
            ]):
                match_id = f"phaseA_{name}_s{base}_k{k}_seed{seed}_o{orientation}"
                row = {"seed": seed, "orientation": orientation, "match_id": match_id, "attempted_hands": match_len}
                try:
                    result = match_mod.run_match(match_id, paths, n_hands=match_len, verbose=False, seed=seed)
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
                        per_hand_delta[hand.get("hand_id")] = final_hero_stack - prev_hero_stack
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
                attempted_total += match_len
                hands_total += int(row["hands"])
                match_count += 1
                hero_errors += len(row["hero_errors"])
                opp_errors += len(row["opp_errors"])
            pair_rows = match_rows[-2:]
            samples.append({
                "seed": seed,
                "hands": sum(int(r["hands"]) for r in pair_rows),
                "attempted_hands": 2 * match_len,
                "chip_delta": sum(int(r["hero_chip_delta"]) for r in pair_rows),
                "bb_per_100": bb100(sum(int(r["hero_chip_delta"]) for r in pair_rows), 2 * match_len),
            })
            print(f"[probe] {name} seed={seed} scheduled={attempted_total}/{target_hands} actual={hands_total} bb100={bb100(sum(s['chip_delta'] for s in samples), attempted_total):+.2f}", flush=True)
            k += 1
    finally:
        match_mod.BotProcess = original_bot_process

    decisions = list(LoggingBotProcess.records)
    by_hand: dict[str, list[dict]] = defaultdict(list)
    for rec in decisions:
        hid = rec.get("hand_id")
        rec["hand_delta"] = int(per_hand_delta.get(hid, 0))
        rec["final_hand_chip_delta"] = rec["hand_delta"]
        by_hand[hid].append(rec)

    with decisions_path.open("w", encoding="utf-8") as f:
        for rec in decisions:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    # Cluster losing hands by the last hero decision before the hand ended.
    clusters = defaultdict(lambda: {"count": 0, "chips": 0, "examples": []})
    all_decision_clusters = defaultdict(lambda: {"count": 0, "chips": 0, "examples": []})
    for hand_id, recs in by_hand.items():
        delta = int(per_hand_delta.get(hand_id, 0))
        if delta >= 0 or not recs:
            continue
        last = recs[-1]
        key = (last["street"], last["position_label"], last["true_position_label"], last["action"], last["sizing_bucket"], last["board_texture_tag"])
        bucket = clusters[key]
        bucket["count"] += 1
        bucket["chips"] += delta
        if len(bucket["examples"]) < 5:
            bucket["examples"].append({k: last.get(k) for k in (
                "hand_id", "your_cards", "pot", "amount_owed", "your_stack", "preflop_raise_count", "facing_raise", "action_log_len", "hand_delta"
            )})
        for rec in recs:
            key2 = (rec["street"], rec["position_label"], rec["true_position_label"], rec["action"], rec["sizing_bucket"], rec["board_texture_tag"])
            b2 = all_decision_clusters[key2]
            b2["count"] += 1
            b2["chips"] += delta
            if len(b2["examples"]) < 3:
                b2["examples"].append({k: rec.get(k) for k in (
                    "hand_id", "your_cards", "pot", "amount_owed", "your_stack", "preflop_raise_count", "facing_raise", "action_log_len", "hand_delta"
                )})

    def render_cluster_items(cluster_dict):
        out = []
        for key, data in cluster_dict.items():
            chips = int(data["chips"])
            out.append({
                "street": key[0],
                "position_label": key[1],
                "true_position_label": key[2],
                "action": key[3],
                "sizing_bucket": key[4],
                "board_texture_tag": key[5],
                "count": int(data["count"]),
                "chips": chips,
                "bb_per_100_scheduled": bb100(chips, attempted_total),
                "mbb_per_game_scheduled": mbb_per_game(chips, attempted_total),
                "examples": data["examples"],
            })
        out.sort(key=lambda x: x["chips"])
        return out

    result = {
        "created_at": now_iso(),
        "name": name,
        "repo": repo,
        "head_sha": head_sha,
        "bot_path": bot_path,
        "hero_zip": str(HERO_ZIP),
        "hero_zip_info": hero_info,
        "opponent_zip": str(opp_zip),
        "opponent_zip_info": opp_zip_info,
        "base": base,
        "target_hands": target_hands,
        "match_len": match_len,
        "seed_stride": seed_stride,
        "attempted_hands": attempted_total,
        "hands_played": hands_total,
        "matches": match_count,
        "hero_chip_delta": sum(s["chip_delta"] for s in samples),
        "hero_bb_per_100_scheduled": bb100(sum(s["chip_delta"] for s in samples), attempted_total),
        "hero_bb_per_100_actual": bb100(sum(s["chip_delta"] for s in samples), hands_total),
        "hero_errors": hero_errors,
        "opp_errors": opp_errors,
        "decision_count": len(decisions),
        "losing_last_decision_clusters": render_cluster_items(clusters),
        "losing_all_decision_clusters": render_cluster_items(all_decision_clusters),
        "match_rows": match_rows,
        "samples": samples,
        "paths": {
            "decisions_jsonl": str(decisions_path),
            "match_json": str(match_json_path),
            "cluster_json": str(summary_path),
        },
    }
    match_json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary_path.write_text(json.dumps({k: result[k] for k in (
        "created_at", "name", "attempted_hands", "hands_played", "hero_chip_delta", "hero_bb_per_100_scheduled",
        "hero_bb_per_100_actual", "hero_errors", "opp_errors", "decision_count", "losing_last_decision_clusters",
        "losing_all_decision_clusters", "paths")}, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "attempted_hands": attempted_total,
        "hands_played": hands_total,
        "hero_bb_per_100_scheduled": result["hero_bb_per_100_scheduled"],
        "decision_count": len(decisions),
        "top_last_clusters": result["losing_last_decision_clusters"][:3],
        "paths": result["paths"],
    }, indent=2), flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="mehedi_mybot")
    parser.add_argument("--opp-zip", type=Path, default=DEFAULT_OPP_ZIP)
    parser.add_argument("--repo", default="Mehedi-dev-2404/fullhouse-engine")
    parser.add_argument("--head-sha", default="aa14a35a4f185f8608ae962aef17a7c620909a4b")
    parser.add_argument("--bot-path", default="bots/mybot/bot.py")
    parser.add_argument("--base", type=int, default=142)
    parser.add_argument("--hands", type=int, default=20000)
    parser.add_argument("--match-len", type=int, default=500)
    parser.add_argument("--seed-stride", type=int, default=1000)
    args = parser.parse_args()
    run_probe(args.name, args.opp_zip, args.repo, args.head_sha, args.bot_path, args.base, args.hands, args.match_len, args.seed_stride)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
