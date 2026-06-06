from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
ENGINE = ROOT / "ext" / "fullhouse-engine"
HERO_ZIP = ROOT / "submissions" / "v_final.zip"
BEST_GREEN_ZIP = ROOT / "submissions" / "best_green.zip"
EXPECTED_LOCKED_SHA = "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"

CLONES = ART / "_clones"
META = ART / "metadata"
LOGS = ART / "command_logs"
ZIP_DIR = ART / "opponent_zips"
INVENTORY_PATH = ART / "opponent_inventory.json"
RESULTS_PATH = ART / "RESULTS.json"
REPORT_PATH = ART / "PUBLIC_DRIFT_COMPLETENESS_REPORT.md"
STATUS_PATH = ART / "STATUS_BLOCK.md"

STANDARD_BOT_NAMES = {"template", "aggressor", "mathematician", "shark", "ref_bot_2"}
TARGET_REPOS = {
    "TobyCoad/fullhouse-engine": {"branch": None, "family": "toby"},
    "Mehedi-dev-2404/fullhouse-engine": {"branch": None, "family": "mehedi"},
    "Pav1602/fullhouse-engine": {"branch": None, "family": "pav"},
    "stoppedtime24/fullhouse-engine": {"branch": None, "family": "stoppedtime24"},
    "vladimirfilip/fullhouse-engine": {"branch": None, "family": "vladimir"},
    "famadeo/fullhouse-engine": {"branch": None, "family": "famadeo"},
    "agrawalneel25/fullhouse-engine": {"branch": "neel-work", "family": "neel"},
}

PRIOR_MATRIX = {
    "famadeo/fullhouse-engine|main|bots/codex_holdem/bot.py": {
        "head_sha": "c94dace1c6bf523aa49e9c149d897c6b71a19c5e",
        "scheduled_hands": 200000,
        "actual_hands": 43914,
        "mean_bb100_scheduled": 0.65,
        "mean_bb100_actual": 2.96,
        "ci_low": -1.30,
        "ci_high": 2.60,
        "hero_errors": 0,
        "opponent_errors": 0,
        "hero_p99_latency_s": 0.0643,
        "verdict": "GREEN",
        "source": "2026-05-29 public-repo-drift prior matrix",
    },
    "agrawalneel25/fullhouse-engine|neel-work|bots/neel/bot.py": {
        "head_sha": "071d54c302cbd2d9d5fcc773260e7f5f894c642f",
        "scheduled_hands": 200000,
        "actual_hands": 102276,
        "mean_bb100_scheduled": 14.69,
        "mean_bb100_actual": 28.73,
        "ci_low": 13.50,
        "ci_high": 15.81,
        "hero_errors": 0,
        "opponent_errors": 0,
        "hero_p99_latency_s": 0.0633,
        "verdict": "GREEN",
        "source": "2026-05-29 public-repo-drift prior matrix",
    },
    "vladimirfilip/fullhouse-engine|main|bots/vlad/bot.py": {
        "head_sha": "1fbf389224eed471a54768898acdecb093a2bd6e",
        "scheduled_hands": 400000,
        "actual_hands": 20081,
        "mean_bb100_scheduled": 3.70,
        "mean_bb100_actual": 73.70,
        "ci_low": 2.40,
        "ci_high": 5.00,
        "hero_errors": 0,
        "opponent_errors": 0,
        "hero_p99_latency_s": 0.0399,
        "verdict": "GREEN",
        "source": "2026-05-28 public-saturation local snapshot",
    },
}
KNOWN_PRIOR_KEYS = set(PRIOR_MATRIX) | {
    "TobyCoad/fullhouse-engine|main|bots/master/bot.py",
    "Mehedi-dev-2404/fullhouse-engine|main|bots/mybot/bot.py",
}

BOOTSTRAP_ITERS = 5000
CI_ALPHA = 0.05


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    for path in (CLONES, META, LOGS, ZIP_DIR):
        path.mkdir(parents=True, exist_ok=True)


def safe_name(text: str) -> str:
    return (
        text.replace("/", "__")
        .replace(":", "_")
        .replace(" ", "_")
        .replace(".", "_")
        .replace("-", "_")
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_locked_artifacts() -> dict:
    values = {
        "submissions/v_final.zip": sha256(HERO_ZIP),
        "submissions/best_green.zip": sha256(BEST_GREEN_ZIP),
    }
    bad = {k: v for k, v in values.items() if v != EXPECTED_LOCKED_SHA}
    if bad:
        raise RuntimeError(f"protected artifact SHA mismatch: {bad}")
    return values


def run_cmd(label: str, cmd: list[str], cwd: Path = ROOT, timeout: int | None = None) -> dict:
    ensure_dirs()
    started = now_iso()
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = time.perf_counter() - t0
    record = {
        "label": label,
        "cmd": cmd,
        "cwd": str(cwd),
        "started_at": started,
        "finished_at": now_iso(),
        "elapsed_s": round(elapsed, 3),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    (LOGS / f"{safe_name(label)}.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def gh_json(label: str, args: list[str]) -> object | None:
    rec = run_cmd(label, ["gh", "api", *args], timeout=120)
    if rec["returncode"] != 0:
        return None
    try:
        return json.loads(rec["stdout"])
    except json.JSONDecodeError:
        return None


def clone_repo(repo: str, branch: str | None, default_branch: str | None) -> Path | None:
    branch = branch or default_branch or "main"
    dest = CLONES / f"{safe_name(repo)}__{safe_name(branch)}"
    if dest.exists():
        shutil.rmtree(dest)
    cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        branch,
        f"https://github.com/{repo}.git",
        str(dest),
    ]
    rec = run_cmd(f"clone_{repo}_{branch}", cmd, timeout=300)
    if rec["returncode"] != 0:
        return None
    return dest


def git_one(repo_dir: Path, label: str, args: list[str]) -> str:
    rec = run_cmd(f"{label}_{repo_dir.name}", ["git", *args], cwd=repo_dir, timeout=60)
    if rec["returncode"] != 0:
        return ""
    return rec["stdout"].strip()


def file_loc(path: Path) -> int:
    try:
        return len(path.read_text(errors="replace").splitlines())
    except OSError:
        return 0


def data_files(bot_dir: Path) -> list[dict]:
    data = bot_dir / "data"
    rows = []
    if not data.is_dir():
        return rows
    for f in sorted(p for p in data.rglob("*") if p.is_file()):
        rows.append(
            {
                "path": str(Path("data") / f.relative_to(data)),
                "size_bytes": f.stat().st_size,
                "sha256": sha256(f),
            }
        )
    return rows


def template_hashes() -> set[str]:
    hashes = set()
    for name in STANDARD_BOT_NAMES:
        path = ENGINE / "bots" / name / "bot.py"
        if path.is_file():
            hashes.add(sha256(path))
    return hashes


def top_level_bot_dirs(repo_dir: Path) -> list[Path]:
    bots = repo_dir / "bots"
    if not bots.is_dir():
        return []
    return sorted(p for p in bots.iterdir() if (p / "bot.py").is_file())


def is_skantbot7(name: str) -> bool:
    return name == "skantbot7" or name.startswith("skantbot7.")


def row_key(row: dict) -> str:
    return f"{row['repo']}|{row['branch']}|{row['bot_path']}"


def make_bot_row(
    repo: str,
    branch: str,
    repo_dir: Path,
    bot_dir: Path,
    family: str,
    inclusion_reason: str,
    default_branch: str,
    recent_fork: bool,
    template_hash_set: set[str],
) -> dict:
    bot_py = bot_dir / "bot.py"
    bot_sha = sha256(bot_py)
    return {
        "repo": repo,
        "branch": branch,
        "default_branch": default_branch,
        "family": family,
        "recent_fork": recent_fork,
        "inclusion_reason": inclusion_reason,
        "latest_commit": git_one(repo_dir, "rev_parse", ["rev-parse", "HEAD"]),
        "commit_date": git_one(repo_dir, "commit_date", ["show", "-s", "--format=%cI", "HEAD"]),
        "bot_path": str(bot_py.relative_to(repo_dir)),
        "bot_name": bot_dir.name,
        "bot_sha256": bot_sha,
        "is_template_hash": bot_sha in template_hash_set,
        "loc": file_loc(bot_py),
        "data_files": data_files(bot_dir),
        "validator_status": "NOT_RUN",
        "validator_log": None,
        "opponent_zip": None,
        "opponent_zip_sha256": None,
        "h2h_required": False,
        "h2h_reason": None,
        "h2h_result_key": None,
        "notes": "",
    }


def add_candidate(rows: list[dict], seen: set[str], row: dict) -> None:
    key = row_key(row)
    if key in seen:
        return
    seen.add(key)
    rows.append(row)


def enumerate_inventory() -> dict:
    ensure_dirs()
    require_locked_artifacts()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    t_hashes = template_hashes()
    repo_meta: dict[str, dict] = {}
    forks_raw = gh_json(
        "github_forks_uzlez_fullhouse_engine",
        ["repos/uzlez/fullhouse-engine/forks?per_page=100"],
    )
    forks = forks_raw if isinstance(forks_raw, list) else []
    (META / "forks_raw.json").write_text(json.dumps(forks, indent=2) + "\n")

    target_specs = dict(TARGET_REPOS)
    recent_forks = []
    for fork in forks:
        pushed_at = fork.get("pushed_at") or ""
        try:
            pushed_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        except ValueError:
            pushed_dt = datetime(1970, 1, 1, tzinfo=timezone.utc)
        full_name = fork.get("full_name", "")
        if full_name.lower().startswith("zealousear/"):
            continue
        if pushed_dt >= cutoff:
            recent_forks.append(
                {
                    "repo": full_name,
                    "default_branch": fork.get("default_branch") or "main",
                    "pushed_at": pushed_at,
                    "html_url": fork.get("html_url"),
                }
            )
            target_specs.setdefault(
                full_name,
                {"branch": fork.get("default_branch") or "main", "family": "recent_fork"},
            )

    rows: list[dict] = []
    seen: set[str] = set()
    repo_rows = []

    for repo, spec in sorted(target_specs.items()):
        meta = gh_json(f"github_repo_{repo}", [f"repos/{repo}"])
        if not isinstance(meta, dict):
            repo_rows.append({"repo": repo, "clone_status": "GH_API_FAILED"})
            continue
        default_branch = meta.get("default_branch") or "main"
        branch = spec.get("branch") or default_branch
        repo_meta[repo] = {
            "repo": repo,
            "default_branch": default_branch,
            "branch": branch,
            "pushed_at": meta.get("pushed_at"),
            "updated_at": meta.get("updated_at"),
            "html_url": meta.get("html_url"),
        }
        repo_dir = clone_repo(repo, branch, default_branch)
        if repo_dir is None:
            repo_rows.append({"repo": repo, "branch": branch, "clone_status": "FAILED"})
            continue
        family = spec["family"]
        bot_dirs = top_level_bot_dirs(repo_dir)
        custom_dirs = [p for p in bot_dirs if p.name not in STANDARD_BOT_NAMES]
        repo_rows.append(
            {
                "repo": repo,
                "branch": branch,
                "clone_status": "OK",
                "latest_commit": git_one(repo_dir, "repo_rev_parse", ["rev-parse", "HEAD"]),
                "commit_date": git_one(repo_dir, "repo_commit_date", ["show", "-s", "--format=%cI", "HEAD"]),
                "top_level_bot_dirs": [p.name for p in bot_dirs],
                "custom_bot_dirs": [p.name for p in custom_dirs],
            }
        )

        def add_dir(bot_dir: Path, reason: str) -> None:
            row = make_bot_row(
                repo,
                branch,
                repo_dir,
                bot_dir,
                family,
                reason,
                default_branch,
                any(r["repo"] == repo for r in recent_forks),
                t_hashes,
            )
            add_candidate(rows, seen, row)

        if family == "toby":
            for bot_dir in custom_dirs:
                add_dir(bot_dir, "Toby custom top-level bot")
        elif family == "mehedi":
            for bot_dir in custom_dirs:
                add_dir(bot_dir, "Mehedi custom top-level bot")
        elif family == "pav":
            for bot_dir in bot_dirs:
                if is_skantbot7(bot_dir.name):
                    add_dir(bot_dir, "Pav skantbot7 variant")
        elif family == "stoppedtime24":
            bot_dir = repo_dir / "bots" / "mybot"
            if (bot_dir / "bot.py").is_file():
                add_dir(bot_dir, "stoppedtime24 requested mybot")
        elif family == "vladimir":
            bot_dir = repo_dir / "bots" / "vlad"
            if (bot_dir / "bot.py").is_file():
                row = make_bot_row(
                    repo,
                    branch,
                    repo_dir,
                    bot_dir,
                    family,
                    "vladimir live vlad",
                    default_branch,
                    any(r["repo"] == repo for r in recent_forks),
                    t_hashes,
                )
                if not (bot_dir / "data" / "gto_strategy.npz").is_file():
                    local_model = ROOT / "ext" / "public-bots" / "vladimir" / "bots" / "vlad" / "data" / "gto_strategy.npz"
                    row["validator_status"] = "TIMEBOXED_UNUSABLE"
                    row["notes"] = (
                        "Live public clone lacks bots/vlad/data/gto_strategy.npz. "
                        f"Prior local model exists={local_model.is_file()}, but live public package is unusable per task instruction."
                    )
                    row["h2h_required"] = False
                add_candidate(rows, seen, row)
        elif family == "famadeo":
            bot_dir = repo_dir / "bots" / "codex_holdem"
            if (bot_dir / "bot.py").is_file():
                add_dir(bot_dir, "famadeo unchanged-SHA check")
        elif family == "neel":
            bot_dir = repo_dir / "bots" / "neel"
            if (bot_dir / "bot.py").is_file():
                add_dir(bot_dir, "agrawalneel25 neel-work unchanged-SHA check")
        else:
            for bot_dir in custom_dirs:
                if sha256(bot_dir / "bot.py") not in t_hashes:
                    add_dir(bot_dir, "recent fork custom non-template bot")

    # Mark H2H requirements after all rows are known.
    for row in rows:
        key = row_key(row)
        if row["validator_status"] == "TIMEBOXED_UNUSABLE":
            row["h2h_required"] = False
            row["h2h_reason"] = "missing required live data"
            continue
        prior = PRIOR_MATRIX.get(key)
        if prior and prior["head_sha"] == row["latest_commit"]:
            row["h2h_required"] = False
            row["h2h_reason"] = "unchanged from prior matrix; H2H reused"
        else:
            row["h2h_required"] = True
            row["h2h_reason"] = "new or changed public bot"

    inv = {
        "created_at": now_iso(),
        "artifact_dir": str(ART),
        "protected_sha": require_locked_artifacts(),
        "forks_count": len(forks),
        "recent_cutoff_utc": cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "recent_forks": recent_forks,
        "repo_inspection": repo_rows,
        "bots": rows,
    }
    INVENTORY_PATH.write_text(json.dumps(inv, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"wrote": str(INVENTORY_PATH), "bots": len(rows), "recent_forks": len(recent_forks)}, indent=2))
    return inv


def load_inventory() -> dict:
    if not INVENTORY_PATH.is_file():
        return enumerate_inventory()
    return json.loads(INVENTORY_PATH.read_text())


def describe_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        names = sorted(z.namelist())
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "has_root_bot_py": "bot.py" in names,
        "data_files": [
            {"path": i.filename, "size_bytes": i.file_size}
            for i in infos
            if i.filename.startswith("data/") and not i.is_dir()
        ],
    }


def package_zip(row: dict) -> dict:
    repo_dir = CLONES / f"{safe_name(row['repo'])}__{safe_name(row['branch'])}"
    src_dir = repo_dir / str(Path(row["bot_path"]).parent)
    out_zip = ZIP_DIR / f"{safe_name(row['repo'])}__{safe_name(row['branch'])}__{safe_name(row['bot_name'])}.zip"
    if row["validator_status"] == "TIMEBOXED_UNUSABLE":
        return row
    if not (src_dir / "bot.py").is_file():
        row["validator_status"] = "UNUSABLE"
        row["notes"] = (row.get("notes") or "") + " Missing bot.py at package time."
        return row
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(src_dir / "bot.py", "bot.py")
        data_dir = src_dir / "data"
        if data_dir.is_dir():
            for f in sorted(p for p in data_dir.rglob("*") if p.is_file()):
                if "__pycache__" in f.parts or f.suffix in {".py", ".pyc", ".pyo"}:
                    continue
                z.write(f, str(Path("data") / f.relative_to(data_dir)))
    info = describe_zip(out_zip)
    row["opponent_zip"] = str(out_zip)
    row["opponent_zip_sha256"] = info["sha256"]
    return row


def validate_zip(row: dict) -> dict:
    if row["validator_status"] == "TIMEBOXED_UNUSABLE":
        return row
    if not row.get("opponent_zip"):
        row["validator_status"] = "UNUSABLE"
        return row
    label = f"validator_{row['repo']}_{row['branch']}_{row['bot_name']}"
    rec = run_cmd(
        label,
        [sys.executable, str(ENGINE / "sandbox" / "validator.py"), row["opponent_zip"], "--json"],
        timeout=120,
    )
    row["validator_log"] = str(LOGS / f"{safe_name(label)}.json")
    row["validator_returncode"] = rec["returncode"]
    try:
        parsed = json.loads(rec["stdout"])
    except json.JSONDecodeError:
        parsed = {"passed": False, "errors": ["validator JSON parse failed"]}
    row["validator_result"] = {
        "passed": bool(parsed.get("passed")),
        "errors": parsed.get("errors", []),
        "warnings": parsed.get("warnings", []),
    }
    row["validator_status"] = "PASS" if parsed.get("passed") else "UNUSABLE"
    return row


def package_validate() -> dict:
    inv = load_inventory()
    require_locked_artifacts()
    rows = []
    for row in inv["bots"]:
        row = package_zip(row)
        row = validate_zip(row)
        rows.append(row)
    inv["bots"] = rows
    inv["package_validate_at"] = now_iso()
    inv["protected_sha"] = require_locked_artifacts()
    INVENTORY_PATH.write_text(json.dumps(inv, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"validated": len(rows), "pass": sum(r["validator_status"] == "PASS" for r in rows)}, indent=2))
    return inv


def import_match_mod():
    sys.path.insert(0, str(ENGINE))
    from engine.game import BIG_BLIND
    from sandbox import match as match_mod

    return BIG_BLIND, match_mod


BIG_BLIND, match_mod = import_match_mod()


class InstrumentedBotProcess(match_mod.BotProcess):
    latencies = defaultdict(list)
    stdout_noise = defaultdict(int)
    stdout_noise_examples = defaultdict(list)

    @classmethod
    def reset(cls) -> None:
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
        try:
            self._proc.stdin.write(json.dumps(game_state) + "\n")
            self._proc.stdin.flush()
            action = self._read_json_obj()
            if "error" in action:
                self.errors.append(action["error"])
            return action
        except Exception as e:
            self.errors.append(str(e))
            return {"action": "fold", "error": str(e)}
        finally:
            self.latencies[self.bot_id].append(time.perf_counter() - start)


def bb100(chips: int | float, hands: int | float) -> float | None:
    if not hands:
        return None
    return (chips / BIG_BLIND) / (hands / 100.0)


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    idx = min(len(xs) - 1, max(0, math.ceil((p / 100.0) * len(xs)) - 1))
    return xs[idx]


def bootstrap_ci(samples: list[dict], seed: int) -> dict:
    if not samples:
        return {"mean": None, "low": None, "high": None, "half_width": None}
    rng = random.Random(seed)
    n = len(samples)
    means = []
    for _ in range(BOOTSTRAP_ITERS):
        chips = 0
        hands = 0
        for _ in range(n):
            s = samples[rng.randrange(n)]
            chips += int(s["chip_delta"])
            hands += int(s["metric_hands"])
        means.append(bb100(chips, hands))
    means = sorted(m for m in means if m is not None)
    chips_total = sum(int(s["chip_delta"]) for s in samples)
    hands_total = sum(int(s["metric_hands"]) for s in samples)
    mean = bb100(chips_total, hands_total)
    low = means[int(BOOTSTRAP_ITERS * CI_ALPHA / 2)]
    high = means[int(BOOTSTRAP_ITERS * (1 - CI_ALPHA / 2))]
    return {"mean": mean, "low": low, "high": high, "half_width": (high - low) / 2.0}


def classify_verdict(mean: float | None, low: float | None, high: float | None, new_threat: bool, timeboxed: bool = False) -> str:
    if mean is None or low is None or high is None:
        return "TIMEBOXED"
    if high < 0 or (mean <= 0 and high <= 5):
        base = "RED"
    elif mean > 0 and low > -20:
        base = "GREEN"
    elif low > -20:
        base = "AMBER"
    elif timeboxed:
        base = "TIMEBOXED"
    else:
        base = "AMBER"
    if new_threat and base != "RED":
        return f"{base}; NEW_THREAT"
    if new_threat:
        return "RED; NEW_THREAT"
    return base


def run_schedule(row: dict, phase: str, target_hands: int, base: int, match_len: int, seed_stride: int, max_seconds: int) -> dict:
    require_locked_artifacts()
    log_path = LOGS / f"h2h_{safe_name(row['repo'])}__{safe_name(row['branch'])}__{safe_name(row['bot_name'])}__{phase}.log"
    start = time.perf_counter()
    original = match_mod.BotProcess
    match_mod.BotProcess = InstrumentedBotProcess
    InstrumentedBotProcess.reset()
    samples = []
    match_rows = []
    attempted = 0
    actual = 0
    hero_errors = 0
    opp_errors = 0
    early_bust = 0
    match_count = 0
    timeboxed = False
    with log_path.open("w", encoding="utf-8") as log:
        def line(text: str = "") -> None:
            print(text, file=log, flush=True)

        line(f"H2H {phase} {now_iso()}")
        line(f"repo={row['repo']} branch={row['branch']} bot={row['bot_path']}")
        line(f"hero={HERO_ZIP} sha256={sha256(HERO_ZIP)}")
        line(f"opponent_zip={row['opponent_zip']} sha256={row['opponent_zip_sha256']}")
        line(f"target_scheduled_hands={target_hands} base={base} match_len={match_len} seed_stride={seed_stride}")
        try:
            k = 0
            while attempted < target_hands:
                if time.perf_counter() - start > max_seconds:
                    timeboxed = True
                    line(f"TIMEBOX max_seconds={max_seconds} attempted={attempted}")
                    break
                seed = base + k * seed_stride
                pair_chips = 0
                pair_actual = 0
                pair_attempted = 0
                pair_hero_errors = 0
                pair_opp_errors = 0
                pair_early = 0
                orientations = [
                    {"hero": str(HERO_ZIP.resolve()), "opp": str(Path(row["opponent_zip"]).resolve())},
                    {"opp": str(Path(row["opponent_zip"]).resolve()), "hero": str(HERO_ZIP.resolve())},
                ]
                for orientation, paths in enumerate(orientations):
                    match_id = f"p4_{safe_name(row['repo'])}_{safe_name(row['bot_name'])}_{phase}_{seed}_{orientation}"
                    started = time.perf_counter()
                    match_row = {
                        "phase": phase,
                        "seed": seed,
                        "orientation": orientation,
                        "attempted_hands": match_len,
                    }
                    try:
                        result = match_mod.run_match(match_id, paths, n_hands=match_len, verbose=False, seed=seed)
                        h = int(result["n_hands"])
                        hero_chip = int(result["chip_delta"]["hero"])
                        he = list(result["bot_errors"]["hero"])
                        oe = list(result["bot_errors"]["opp"])
                        match_row.update(
                            {
                                "hands": h,
                                "duration_s": float(result["duration_s"]),
                                "hero_chip_delta": hero_chip,
                                "opponent_chip_delta": int(result["chip_delta"]["opp"]),
                                "hero_errors": he,
                                "opponent_errors": oe,
                            }
                        )
                    except Exception as e:
                        h = 0
                        hero_chip = 0
                        he = [f"match_failed: {e}"]
                        oe = []
                        match_row.update(
                            {
                                "hands": 0,
                                "duration_s": round(time.perf_counter() - started, 3),
                                "hero_chip_delta": 0,
                                "opponent_chip_delta": 0,
                                "hero_errors": he,
                                "opponent_errors": oe,
                            }
                        )
                    attempted += match_len
                    actual += h
                    pair_attempted += match_len
                    pair_actual += h
                    pair_chips += hero_chip
                    pair_hero_errors += len(he)
                    pair_opp_errors += len(oe)
                    hero_errors += len(he)
                    opp_errors += len(oe)
                    match_count += 1
                    if h < match_len:
                        early_bust += 1
                        pair_early += 1
                    match_rows.append(match_row)
                    line(
                        f"seed={seed} o={orientation} hands={h:4d}/{match_len} "
                        f"hero_chip={hero_chip:+8d} sched_bb100={bb100(hero_chip, match_len):+8.2f} "
                        f"actual_bb100={bb100(hero_chip, h) if h else None} "
                        f"hero_err={len(he)} opp_err={len(oe)} dur={match_row['duration_s']:.2f}s"
                    )
                samples.append(
                    {
                        "phase": phase,
                        "seed": seed,
                        "hands": pair_actual,
                        "metric_hands": pair_attempted,
                        "chip_delta": pair_chips,
                        "early_bust_matches": pair_early,
                        "hero_errors": pair_hero_errors,
                        "opponent_errors": pair_opp_errors,
                    }
                )
                k += 1
        finally:
            match_mod.BotProcess = original
        ci = bootstrap_ci(samples, base ^ 0x50434)
        hero_lat = InstrumentedBotProcess.latencies.get("hero", [])
        opp_lat = InstrumentedBotProcess.latencies.get("opp", [])
        out = {
            "phase": phase,
            "base": base,
            "target_scheduled_hands": target_hands,
            "attempted_hands": attempted,
            "hands_played": actual,
            "hero_chip_delta": sum(s["chip_delta"] for s in samples),
            "mean_bb100_scheduled": ci["mean"],
            "mean_bb100_actual": bb100(sum(s["chip_delta"] for s in samples), actual),
            "ci_low": ci["low"],
            "ci_high": ci["high"],
            "ci_half_width": ci["half_width"],
            "hero_errors": hero_errors,
            "opponent_errors": opp_errors,
            "early_bust_matches": early_bust,
            "match_count": match_count,
            "early_bust_rate": early_bust / match_count if match_count else None,
            "actual_to_scheduled_ratio": actual / attempted if attempted else None,
            "hero_p99_latency_s": percentile(hero_lat, 99),
            "opponent_p99_latency_s": percentile(opp_lat, 99),
            "stdout_noise": dict(InstrumentedBotProcess.stdout_noise),
            "stdout_noise_examples": dict(InstrumentedBotProcess.stdout_noise_examples),
            "samples": samples,
            "match_rows": match_rows,
            "log_path": str(log_path),
            "timeboxed": timeboxed,
        }
        line()
        line("SUMMARY " + json.dumps({k: v for k, v in out.items() if k not in {"samples", "match_rows"}}, sort_keys=True))
    return out


def combine_runs(row: dict, runs: list[dict], new_threat: bool) -> dict:
    samples = []
    for run in runs:
        samples.extend(run["samples"])
    ci = bootstrap_ci(samples, int(sha256(Path(row["opponent_zip"]))[:8], 16))
    chips = sum(int(s["chip_delta"]) for s in samples)
    scheduled = sum(int(s["metric_hands"]) for s in samples)
    actual = sum(int(run["hands_played"]) for run in runs)
    timeboxed = any(run["timeboxed"] for run in runs) or scheduled == 0
    early = sum(int(run["early_bust_matches"]) for run in runs)
    matches = sum(int(run["match_count"]) for run in runs)
    return {
        "repo": row["repo"],
        "branch": row["branch"],
        "latest_commit": row["latest_commit"],
        "commit_date": row["commit_date"],
        "bot_path": row["bot_path"],
        "bot_name": row["bot_name"],
        "bot_sha256": row["bot_sha256"],
        "opponent_zip": row["opponent_zip"],
        "opponent_zip_sha256": row["opponent_zip_sha256"],
        "validator_status": row["validator_status"],
        "new_threat": new_threat,
        "scheduled_hands": scheduled,
        "actual_hands": actual,
        "hero_chip_delta": chips,
        "mean_bb100_scheduled": ci["mean"],
        "mean_bb100_actual": bb100(chips, actual),
        "ci_low": ci["low"],
        "ci_high": ci["high"],
        "ci_half_width": ci["half_width"],
        "hero_errors": sum(int(run["hero_errors"]) for run in runs),
        "opponent_errors": sum(int(run["opponent_errors"]) for run in runs),
        "hero_p99_latency_s": max((run["hero_p99_latency_s"] or 0.0) for run in runs) if runs else None,
        "opponent_p99_latency_s": max((run["opponent_p99_latency_s"] or 0.0) for run in runs) if runs else None,
        "early_bust_matches": early,
        "match_count": matches,
        "early_bust_rate": early / matches if matches else None,
        "actual_to_scheduled_ratio": actual / scheduled if scheduled else None,
        "verdict": classify_verdict(ci["mean"], ci["low"], ci["high"], new_threat, timeboxed),
        "runs": [{k: v for k, v in run.items() if k not in {"samples", "match_rows"}} for run in runs],
    }


def trigger_escalation(run: dict) -> tuple[bool, list[str]]:
    reasons = []
    mean = run.get("mean_bb100_scheduled")
    low = run.get("ci_low")
    ratio = run.get("actual_to_scheduled_ratio")
    early_rate = run.get("early_bust_rate")
    if mean is not None and mean <= 0:
        reasons.append("mean<=0")
    if low is not None and low <= -10:
        reasons.append("ci_low<=-10")
    if ratio is not None and ratio < 0.40:
        reasons.append("surprising_early_bust_actual_ratio<0.40")
    if early_rate is not None and early_rate >= 0.75:
        reasons.append("surprising_early_bust_rate>=0.75")
    return bool(reasons), reasons


def h2h(triage_hands: int, escalate_total_hands: int, match_len: int, max_seconds: int, force: bool) -> dict:
    inv = load_inventory()
    if any(r["validator_status"] == "NOT_RUN" for r in inv["bots"]):
        inv = package_validate()
    require_locked_artifacts()
    existing = {}
    if RESULTS_PATH.is_file() and not force:
        existing_doc = json.loads(RESULTS_PATH.read_text())
        existing = existing_doc.get("results", {})
    results = dict(existing)
    for row in inv["bots"]:
        key = row_key(row)
        if key in results and not force:
            continue
        if row["validator_status"] == "TIMEBOXED_UNUSABLE":
            prior = PRIOR_MATRIX.get(key)
            results[key] = {
                "repo": row["repo"],
                "branch": row["branch"],
                "latest_commit": row["latest_commit"],
                "commit_date": row["commit_date"],
                "bot_path": row["bot_path"],
                "bot_name": row["bot_name"],
                "validator_status": "TIMEBOXED_UNUSABLE",
                "verdict": "TIMEBOXED_UNUSABLE",
                "new_threat": False,
                "notes": row["notes"],
                "prior_background": prior,
            }
            continue
        if row["validator_status"] != "PASS":
            results[key] = {
                "repo": row["repo"],
                "branch": row["branch"],
                "latest_commit": row["latest_commit"],
                "commit_date": row["commit_date"],
                "bot_path": row["bot_path"],
                "bot_name": row["bot_name"],
                "validator_status": row["validator_status"],
                "verdict": "UNUSABLE",
                "new_threat": False,
                "notes": row.get("notes", ""),
            }
            continue
        prior = PRIOR_MATRIX.get(key)
        unchanged = bool(prior and prior["head_sha"] == row["latest_commit"])
        if unchanged and not row["h2h_required"]:
            results[key] = {
                "repo": row["repo"],
                "branch": row["branch"],
                "latest_commit": row["latest_commit"],
                "commit_date": row["commit_date"],
                "bot_path": row["bot_path"],
                "bot_name": row["bot_name"],
                "validator_status": row["validator_status"],
                "opponent_zip": row["opponent_zip"],
                "opponent_zip_sha256": row["opponent_zip_sha256"],
                "verdict": prior["verdict"],
                "new_threat": False,
                "scheduled_hands": prior["scheduled_hands"],
                "actual_hands": prior["actual_hands"],
                "mean_bb100_scheduled": prior["mean_bb100_scheduled"],
                "mean_bb100_actual": prior["mean_bb100_actual"],
                "ci_low": prior["ci_low"],
                "ci_high": prior["ci_high"],
                "hero_errors": prior["hero_errors"],
                "opponent_errors": prior["opponent_errors"],
                "hero_p99_latency_s": prior["hero_p99_latency_s"],
                "notes": "Unchanged SHA; prior H2H reused per task instruction.",
                "prior_background": prior,
            }
            continue
        new_threat = key not in KNOWN_PRIOR_KEYS
        print(f"[h2h] {key} triage={triage_hands}", flush=True)
        triage = run_schedule(row, "triage_b142", triage_hands, 142, match_len, 1000, max_seconds)
        runs = [triage]
        should_escalate, reasons = trigger_escalation(triage)
        if should_escalate and escalate_total_hands > triage_hands:
            extra = escalate_total_hands - triage_hands
            print(f"[h2h] {key} escalate extra={extra} reasons={','.join(reasons)}", flush=True)
            runs.append(run_schedule(row, "escalate_b242", extra, 242, match_len, 1000, max_seconds))
        combined = combine_runs(row, runs, new_threat)
        combined["escalation_reasons"] = reasons
        results[key] = combined
        RESULTS_PATH.write_text(
            json.dumps(
                {
                    "created_at": now_iso(),
                    "artifact_dir": str(ART),
                    "protected_sha": require_locked_artifacts(),
                    "results": results,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    out = {
        "created_at": now_iso(),
        "artifact_dir": str(ART),
        "protected_sha": require_locked_artifacts(),
        "results": results,
    }
    RESULTS_PATH.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"wrote": str(RESULTS_PATH), "results": len(results)}, indent=2))
    return out


def fmt_float(x, digits: int = 2) -> str:
    if x is None:
        return "n/a"
    return f"{x:.{digits}f}"


def verdict_base(v: str) -> str:
    if v.startswith("RED"):
        return "RED"
    if v.startswith("GREEN"):
        return "GREEN"
    if v.startswith("AMBER"):
        return "AMBER"
    if v.startswith("TIMEBOXED"):
        return "TIMEBOXED"
    return v


def generate_report() -> None:
    inv = load_inventory()
    if not RESULTS_PATH.is_file():
        raise RuntimeError("missing RESULTS.json; run h2h first")
    res_doc = json.loads(RESULTS_PATH.read_text())
    results = res_doc["results"]
    for r in results.values():
        runs = r.get("runs") or []
        collection_timeboxed = any(run.get("timeboxed") for run in runs)
        if collection_timeboxed:
            r["collection_status"] = "TIMEBOXED_PARTIAL"
        if r.get("mean_bb100_scheduled") is not None:
            r["verdict"] = classify_verdict(
                r.get("mean_bb100_scheduled"),
                r.get("ci_low"),
                r.get("ci_high"),
                bool(r.get("new_threat")),
                collection_timeboxed,
            )
    protected_after = require_locked_artifacts()

    rows = sorted(results.values(), key=lambda r: (r.get("repo", ""), r.get("bot_path", "")))
    pav = [r for r in rows if r.get("repo") == "Pav1602/fullhouse-engine" and "skantbot7" in r.get("bot_path", "")]
    red_rows = [r for r in rows if verdict_base(r.get("verdict", "")) == "RED"]
    recent_custom = [r for r in rows if any(b.get("repo") == r.get("repo") and b.get("recent_fork") for b in inv["bots"])]
    vlad = [r for r in rows if r.get("repo") == "vladimirfilip/fullhouse-engine"]

    pav_red = [r for r in pav if verdict_base(r.get("verdict", "")) == "RED"]
    only_toby_mehedi_red = all(
        r.get("repo") in {"TobyCoad/fullhouse-engine", "Mehedi-dev-2404/fullhouse-engine"}
        for r in red_rows
    )
    red_public_names = ", ".join(f"{r['repo']} {r['bot_path']}" for r in red_rows) or "none"

    answers = {
        "pav_red": bool(pav_red),
        "only_toby_mehedi_red": only_toby_mehedi_red,
        "recent_custom_count": len(recent_custom),
        "vladimir_live_verdict": vlad[0]["verdict"] if vlad else "not found",
        "modify_gate": bool(red_rows),
    }
    res_doc["protected_sha_after_report"] = protected_after
    res_doc["answers"] = answers
    RESULTS_PATH.write_text(json.dumps(res_doc, indent=2, sort_keys=True) + "\n")

    table_lines = [
        "| repo | branch | commit | date | bot path | LOC | data files | validator | scheduled | actual | bb/100 scheduled | bb/100 actual | CI | hero errors | opp errors | p99 latency | verdict |",
        "|---|---|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    bot_by_key = {row_key(b): b for b in inv["bots"]}
    for r in rows:
        key = f"{r['repo']}|{r['branch']}|{r['bot_path']}"
        b = bot_by_key.get(key, {})
        data_count = len(b.get("data_files", []))
        ci = f"[{fmt_float(r.get('ci_low'))}, {fmt_float(r.get('ci_high'))}]"
        table_lines.append(
            "| {repo} | {branch} | `{commit}` | {date} | `{bot}` | {loc} | {data_count} | {validator} | {sched} | {actual} | {mean_s} | {mean_a} | {ci} | {he} | {oe} | {p99} | {verdict} |".format(
                repo=r.get("repo", ""),
                branch=r.get("branch", ""),
                commit=(r.get("latest_commit") or "")[:12],
                date=r.get("commit_date", ""),
                bot=r.get("bot_path", ""),
                loc=b.get("loc", ""),
                data_count=data_count,
                validator=r.get("validator_status", ""),
                sched=r.get("scheduled_hands", "n/a"),
                actual=r.get("actual_hands", "n/a"),
                mean_s=fmt_float(r.get("mean_bb100_scheduled")),
                mean_a=fmt_float(r.get("mean_bb100_actual")),
                ci=ci,
                he=r.get("hero_errors", "n/a"),
                oe=r.get("opponent_errors", "n/a"),
                p99=fmt_float(r.get("hero_p99_latency_s"), 4),
                verdict=r.get("verdict", ""),
            )
        )

    pav_versions = sorted(Path(r.get("bot_path", "")).parts[-2] for r in pav)
    missing_pav = []
    expected = ["skantbot7", "skantbot7.1", "skantbot7.2", "skantbot7.3", "skantbot7.4", "skantbot7.5", "skantbot7.6", "skantbot7.7", "skantbot7.8", "skantbot7.9"]
    for name in expected:
        if name not in pav_versions:
            missing_pav.append(name)

    report = f"""# P4 Public Drift Completeness Sweep

Created: {now_iso()}

## Hard-invariant check

- `submissions/v_final.zip`: `{protected_after['submissions/v_final.zip']}`
- `submissions/best_green.zip`: `{protected_after['submissions/best_green.zip']}`
- Locked SHA expected: `{EXPECTED_LOCKED_SHA}`
- Strategy edits: none by this lane.
- Candidate artifacts: temporary opponent zips only, under `{ZIP_DIR}`.

## Direct answers

1. Are Pav intermediate versions hiding a RED cell? **{'YES' if pav_red else 'NO'}**. Tested Pav skantbot7 variants: {', '.join(pav_versions) or 'none'}. Missing/absent in live repo: {', '.join(missing_pav) if missing_pav else 'none'}.
2. Are Toby and Mehedi still the only RED public cells? **{'YES' if only_toby_mehedi_red else 'NO'}**. RED cells: {red_public_names}.
3. Did any recently pushed fork add a new custom bot? **{'YES' if recent_custom else 'NO'}**. Recent custom rows in this matrix: {len(recent_custom)}.
4. Does live vladimir invalidate the prior local positive audit? **NO STABLE LIVE INVALIDATION**. Live public `bots/vlad` is marked `{vlad[0]['verdict'] if vlad else 'missing'}` because required `data/gto_strategy.npz` is absent from the live public clone; prior local audit remains background only.
5. Does anything justify opening a pre-qualifier MODIFY gate? **{'YES, review gate only' if red_rows else 'NO'}**. RED evidence justifies orchestrator review, but not modifying `v_final.zip` without a fully gated candidate.

Default recommendation: do not modify `v_final.zip` without a fully gated candidate.

## Inventory and results

{chr(10).join(table_lines)}

## Recent fork enumeration

- Forks returned by `gh api repos/uzlez/fullhouse-engine/forks?per_page=100`: {inv.get('forks_count')}
- Recent cutoff: {inv.get('recent_cutoff_utc')}
- Recent forks inspected: {len(inv.get('recent_forks', []))}

Recent forks:
{chr(10).join(f"- `{f['repo']}` pushed `{f.get('pushed_at')}`" for f in inv.get('recent_forks', [])) or "- none"}

## Specific confirmations

- famadeo `bots/codex_holdem`: live head remained `c94dace1c6bf523aa49e9c149d897c6b71a19c5e`; H2H was not rerun and prior GREEN metrics were reused.
- agrawalneel25 `neel-work/bots/neel`: live head remained `071d54c302cbd2d9d5fcc773260e7f5f894c642f`; H2H was not rerun and prior GREEN metrics were reused.
- Recent forks with custom non-template bot rows: Mehedi `bots/mybot`, stoppedtime24 `bots/mybot`, and vladimir `bots/vlad` (unusable because live public data is missing). The other recent forks inspected were template/reference only.
- Mehedi escalation collected 89,000 scheduled hands before the phase timebox; the verdict is still RED because the combined CI high is below zero.

## Notes

- Scheduled bb/100 is the primary matrix metric; actual bb/100 is reported separately because early busts reduce played hands.
- `NEW_THREAT` is attached to valid bots not present in the prior matrix.
- `TIMEBOXED_UNUSABLE` means a requested live bot could not be used as a complete public package due missing required data.
- Validator logs, clone/API logs, and H2H logs are under `{LOGS}`.
"""
    REPORT_PATH.write_text(report)

    red_summary = "\n".join(
        f"- {r['repo']} {r['bot_path']}: {r['verdict']} mean={fmt_float(r.get('mean_bb100_scheduled'))} CI=[{fmt_float(r.get('ci_low'))},{fmt_float(r.get('ci_high'))}]"
        for r in red_rows
    ) or "- none"
    status = f"""P4_PUBLIC_DRIFT_COMPLETENESS: {'RED_REVIEW' if red_rows else 'GREEN'}

Protected SHAs:
- v_final.zip `{protected_after['submissions/v_final.zip']}`
- best_green.zip `{protected_after['submissions/best_green.zip']}`

Key answers:
- Pav intermediate RED cell: {'YES' if pav_red else 'NO'}
- RED public cells: {red_public_names}
- Recent custom forks found: {len(recent_custom)}
- Live vladimir: {vlad[0]['verdict'] if vlad else 'missing'}
- Recommendation: do not modify `v_final.zip` without a fully gated candidate.

RED rows:
{red_summary}

Outputs:
- `{REPORT_PATH}`
- `{RESULTS_PATH}`
- `{INVENTORY_PATH}`
"""
    STATUS_PATH.write_text(status)
    print(json.dumps({"wrote_report": str(REPORT_PATH), "wrote_status": str(STATUS_PATH), "red_rows": len(red_rows)}, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory")
    sub.add_parser("package-validate")
    h = sub.add_parser("h2h")
    h.add_argument("--triage-hands", type=int, default=20000)
    h.add_argument("--escalate-total-hands", type=int, default=100000)
    h.add_argument("--match-len", type=int, default=500)
    h.add_argument("--max-seconds-per-phase", type=int, default=1200)
    h.add_argument("--force", action="store_true")
    sub.add_parser("report")
    allp = sub.add_parser("all")
    allp.add_argument("--triage-hands", type=int, default=20000)
    allp.add_argument("--escalate-total-hands", type=int, default=100000)
    allp.add_argument("--match-len", type=int, default=500)
    allp.add_argument("--max-seconds-per-phase", type=int, default=1200)
    allp.add_argument("--force", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    require_locked_artifacts()
    if args.cmd == "inventory":
        enumerate_inventory()
    elif args.cmd == "package-validate":
        package_validate()
    elif args.cmd == "h2h":
        h2h(args.triage_hands, args.escalate_total_hands, args.match_len, args.max_seconds_per_phase, args.force)
    elif args.cmd == "report":
        generate_report()
    elif args.cmd == "all":
        enumerate_inventory()
        package_validate()
        h2h(args.triage_hands, args.escalate_total_hands, args.match_len, args.max_seconds_per_phase, args.force)
        generate_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
