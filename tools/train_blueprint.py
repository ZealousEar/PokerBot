"""Train the compact mixed lookup blueprint with deterministic full-tree CFR.

This is deliberately an *offline* trainer.  It solves a tractable Bayesian
one-decision poker abstraction for every public context and ships only the
average hero strategies.  Each abstract game has:

* five private strength buckets for hero and a representative responder;
* fold/check/call plus up to two discrete aggression sizes;
* a responder fold/call node after aggression; and
* exact chance traversal with vanilla CFR regret matching.

It is not a six-player no-limit equilibrium solver.  The artifact records that
scope explicitly so a trained table cannot be mistaken for a Pluribus-scale
blueprint.  The gain over the old placeholder is concrete: optimization runs
for positive iterations, emits average mixed strategies, records convergence
diagnostics, and reproduces byte-for-byte.

Usage:
    python tools/train_blueprint.py --iterations 1200
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.blueprint_policy import (  # noqa: E402
    DEFAULT_ARTIFACT,
    POSTFLOP_PRESSURES,
    POSTFLOP_STREETS,
    POSTFLOP_STRENGTHS,
    POSTFLOP_TEXTURES,
    PREFLOP_POSITIONS,
    PREFLOP_PRESSURES,
    PREFLOP_STRENGTHS,
    SCHEMA_VERSION,
    STACK_BUCKETS,
    postflop_context_key,
    preflop_context_key,
)


DEFAULT_OUTPUT = ROOT / "data" / DEFAULT_ARTIFACT
RESPONSES = ("fold", "call")
MEANINGFUL_MIX_FLOOR = 0.02
PROBABILITY_DIGITS = 8


@dataclass(frozen=True)
class ContextSpec:
    """One public abstract game shared by five hero strength infosets."""

    domain: str
    fields: Tuple[Tuple[str, str], ...]
    strengths: Tuple[str, ...]
    actions: Tuple[str, ...]
    pot: float
    call_cost: float
    action_costs: Tuple[Tuple[str, float], ...]
    hero_prior: Tuple[float, ...]
    villain_prior: Tuple[float, ...]
    passive_realization: float = 1.0

    def action_cost(self, action: str) -> Optional[float]:
        return dict(self.action_costs).get(action)

    def row_key(self, strength: str) -> str:
        values = dict(self.fields)
        if self.domain == "preflop":
            return preflop_context_key(
                values["position"], values["pressure"], values["stack"], strength
            )
        return postflop_context_key(
            values["street"],
            values["texture"],
            values["pressure"],
            values["stack"],
            strength,
        )

    def public_key(self) -> str:
        return "|".join([self.domain] + [f"{key}={value}" for key, value in self.fields])


@dataclass
class SolvedContext:
    hero_average: List[List[float]]
    villain_average: Dict[Tuple[int, int], List[float]]
    initial_gap: float
    final_gap: float
    value: float


def _normalize(values: Sequence[float]) -> Tuple[float, ...]:
    total = float(sum(values))
    if total <= 0.0:
        raise ValueError("chance prior must have positive mass")
    return tuple(float(value) / total for value in values)


def _tilt(values: Sequence[float], amount: float) -> Tuple[float, ...]:
    """Exponentially tilt a five-bucket prior toward high/low strength."""
    center = (len(values) - 1) / 2.0
    tilted = [
        float(value) * math.exp(amount * (index - center))
        for index, value in enumerate(values)
    ]
    return _normalize(tilted)


def _deduplicated_aggressions(
    candidates: Sequence[Tuple[str, float]], call_cost: float
) -> Tuple[Tuple[str, float], ...]:
    """Remove stack-capped duplicate sizes and non-raises."""
    result: List[Tuple[str, float]] = []
    seen_costs: List[float] = []
    for action, raw_cost in candidates:
        cost = round(float(raw_cost), 8)
        if cost <= call_cost + 1e-9:
            continue
        if any(abs(cost - previous) <= 1e-9 for previous in seen_costs):
            continue
        result.append((action, cost))
        seen_costs.append(cost)
    return tuple(result)


def _preflop_spec(position: str, pressure: str, stack: str) -> ContextSpec:
    stack_chips = {"short": 18.0, "medium": 55.0, "deep": 100.0}[stack]
    hero_prior = (0.40, 0.25, 0.20, 0.11, 0.04)
    pressure_priors = {
        "unopened": (0.30, 0.25, 0.21, 0.16, 0.08),
        "limped": (0.38, 0.28, 0.19, 0.11, 0.04),
        "open": (0.18, 0.21, 0.25, 0.23, 0.13),
        "threebet": (0.08, 0.13, 0.22, 0.31, 0.26),
        "fourbet": (0.03, 0.07, 0.13, 0.30, 0.47),
    }
    # Earlier positions face more players and therefore a stronger aggregate
    # continuing range; late/blind positions face a weaker representative.
    position_tilt = {
        "UTG": 0.16,
        "MP": 0.10,
        "CO": 0.03,
        "BTN": -0.08,
        "SB": -0.03,
        "BB": 0.02,
    }[position]
    villain_prior = _tilt(pressure_priors[pressure], position_tilt)

    if pressure == "unopened":
        pot, call_cost = 1.5, 0.0
        if position == "BB":
            passive = ("check",)
            aggressions: Tuple[Tuple[str, float], ...] = ()
        else:
            passive = ("fold",)
            aggressions = _deduplicated_aggressions(
                (
                    ("open_small", min(2.25, stack_chips)),
                    ("open_large", min(3.00, stack_chips)),
                ),
                call_cost,
            )
    elif pressure == "limped":
        pot, call_cost = 2.5, (0.0 if position == "BB" else 1.0)
        passive = (("check",) if position == "BB" else ("fold", "call"))
        aggressions = _deduplicated_aggressions(
            (
                ("iso_small", min(3.5, stack_chips)),
                ("iso_large", min(5.0, stack_chips)),
            ),
            call_cost,
        )
    elif pressure == "open":
        pot, call_cost = 4.5, min(2.5, stack_chips)
        passive = ("fold", "call")
        aggressions = _deduplicated_aggressions(
            (
                ("threebet_small", min(8.0, stack_chips)),
                ("threebet_large", min(11.0, stack_chips)),
            ),
            call_cost,
        )
    elif pressure == "threebet":
        pot, call_cost = 12.0, min(6.5, stack_chips)
        passive = ("fold", "call")
        aggressions = _deduplicated_aggressions(
            (
                ("fourbet_small", min(20.0, stack_chips)),
                ("jam", stack_chips),
            ),
            call_cost,
        )
    else:
        pot, call_cost = 28.0, min(14.0, stack_chips)
        passive = ("fold", "call")
        aggressions = _deduplicated_aggressions(
            (("jam", stack_chips),), call_cost
        )

    action_costs = aggressions
    actions = tuple(passive) + tuple(action for action, _ in aggressions)
    return ContextSpec(
        domain="preflop",
        fields=(("position", position), ("pressure", pressure), ("stack", stack)),
        strengths=PREFLOP_STRENGTHS,
        actions=actions,
        pot=pot,
        call_cost=call_cost,
        action_costs=action_costs,
        hero_prior=_normalize(hero_prior),
        villain_prior=villain_prior,
        passive_realization=0.74,
    )


def _postflop_priors(
    street: str, texture: str, pressure: str
) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
    hero_by_street = {
        "flop": (0.34, 0.25, 0.23, 0.14, 0.04),
        "turn": (0.38, 0.18, 0.25, 0.15, 0.04),
        "river": (0.43, 0.04, 0.29, 0.18, 0.06),
    }
    villain_by_pressure = {
        "free": (0.34, 0.24, 0.23, 0.15, 0.04),
        "small": (0.25, 0.22, 0.25, 0.21, 0.07),
        "medium": (0.18, 0.19, 0.25, 0.27, 0.11),
        # Large bets are polar rather than monotonically strong.
        "large": (0.25, 0.10, 0.10, 0.20, 0.35),
    }
    hero = list(hero_by_street[street])
    villain = list(villain_by_pressure[pressure])
    if texture == "wet":
        hero[1] *= 1.35
        villain[1] *= 1.35
    elif texture == "paired":
        hero[0] *= 1.10
        hero[4] *= 1.18
        villain[0] *= 1.10
        villain[4] *= 1.18
    elif texture == "monotone":
        hero[0] *= 1.18
        hero[3] *= 0.85
        hero[4] *= 1.35
        villain[0] *= 1.18
        villain[3] *= 0.85
        villain[4] *= 1.35
    street_tilt = {"flop": 0.0, "turn": 0.04, "river": 0.08}[street]
    return _normalize(hero), _tilt(villain, street_tilt)


def _postflop_spec(street: str, texture: str, pressure: str, stack: str) -> ContextSpec:
    capacity = {"short": 1.5, "medium": 4.0, "deep": 10.0}[stack]
    hero_prior, villain_prior = _postflop_priors(street, texture, pressure)
    realization = {"flop": 0.72, "turn": 0.84, "river": 1.0}[street]

    if pressure == "free":
        pot, call_cost = 1.0, 0.0
        passive = ("check",)
        aggressions = _deduplicated_aggressions(
            (
                ("bet_small", min(0.33, capacity)),
                ("bet_large", min(0.75, capacity)),
            ),
            call_cost,
        )
    else:
        call_cost = {"small": 0.33, "medium": 0.67, "large": 1.0}[pressure]
        pot = 1.0 + call_cost
        passive = ("fold", "call")
        raise_base = pot + call_cost
        aggressions = _deduplicated_aggressions(
            (
                ("raise_small", min(call_cost + 0.55 * raise_base, capacity)),
                ("raise_large", min(call_cost + 1.00 * raise_base, capacity)),
            ),
            call_cost,
        )

    actions = tuple(passive) + tuple(action for action, _ in aggressions)
    return ContextSpec(
        domain="postflop",
        fields=(
            ("street", street),
            ("texture", texture),
            ("pressure", pressure),
            ("stack", stack),
        ),
        strengths=POSTFLOP_STRENGTHS,
        actions=actions,
        pot=pot,
        call_cost=call_cost,
        action_costs=aggressions,
        hero_prior=hero_prior,
        villain_prior=villain_prior,
        passive_realization=realization,
    )


def build_context_specs() -> List[ContextSpec]:
    """Return the complete, stable public-context grid."""
    result: List[ContextSpec] = []
    for position in PREFLOP_POSITIONS:
        for pressure in PREFLOP_PRESSURES:
            for stack in STACK_BUCKETS:
                result.append(_preflop_spec(position, pressure, stack))
    for street in POSTFLOP_STREETS:
        for texture in POSTFLOP_TEXTURES:
            for pressure in POSTFLOP_PRESSURES:
                for stack in STACK_BUCKETS:
                    result.append(_postflop_spec(street, texture, pressure, stack))
    return result


def _regret_matching(regrets: Sequence[float]) -> List[float]:
    positive = [max(0.0, float(value)) for value in regrets]
    total = sum(positive)
    if total > 1e-15:
        return [value / total for value in positive]
    uniform = 1.0 / len(regrets)
    return [uniform for _ in regrets]


def _win_probability(hero_bucket: int, villain_bucket: int) -> float:
    """Smoothed showdown equity between ordinal strength buckets."""
    by_difference = {
        -4: 0.02,
        -3: 0.06,
        -2: 0.16,
        -1: 0.32,
        0: 0.50,
        1: 0.68,
        2: 0.84,
        3: 0.94,
        4: 0.98,
    }
    return by_difference[hero_bucket - villain_bucket]


def _payoff(
    spec: ContextSpec,
    hero_bucket: int,
    villain_bucket: int,
    action_index: int,
    response: str = "call",
) -> float:
    """Hero's incremental normalized-chip payoff at one terminal."""
    action = spec.actions[action_index]
    equity = _win_probability(hero_bucket, villain_bucket)
    if action == "fold":
        return 0.0
    if action == "check":
        return spec.passive_realization * equity * spec.pot
    if action == "call":
        return equity * spec.pot - (1.0 - equity) * spec.call_cost

    cost = spec.action_cost(action)
    if cost is None:
        raise ValueError(f"aggressive action {action!r} has no cost")
    if response == "fold":
        return spec.pot
    if response != "call":
        raise ValueError(f"unknown response {response!r}")
    # Opponent already invested the amount we are calling in pressure spots;
    # only its additional match to our raise enters future winnings.
    opponent_increment = max(0.0, cost - spec.call_cost)
    return equity * (spec.pot + opponent_increment) - (1.0 - equity) * cost


def _average_rows(sums: Sequence[Sequence[float]]) -> List[List[float]]:
    result: List[List[float]] = []
    for row in sums:
        total = sum(row)
        if total <= 0.0:
            result.append([1.0 / len(row) for _ in row])
        else:
            result.append([value / total for value in row])
    return result


def _profile_gap(
    spec: ContextSpec,
    hero_policy: Sequence[Sequence[float]],
    villain_policy: Mapping[Tuple[int, int], Sequence[float]],
) -> Tuple[float, float]:
    """Return (NashConv-style best-response gap, profile hero value)."""
    hero_br_value = 0.0
    profile_value = 0.0
    for hero_bucket, hero_mass in enumerate(spec.hero_prior):
        action_values: List[float] = []
        for action_index, action in enumerate(spec.actions):
            value = 0.0
            for villain_bucket, villain_mass in enumerate(spec.villain_prior):
                if spec.action_cost(action) is None:
                    terminal = _payoff(
                        spec, hero_bucket, villain_bucket, action_index
                    )
                else:
                    strategy = villain_policy[(villain_bucket, action_index)]
                    terminal = sum(
                        strategy[response_index]
                        * _payoff(
                            spec,
                            hero_bucket,
                            villain_bucket,
                            action_index,
                            response,
                        )
                        for response_index, response in enumerate(RESPONSES)
                    )
                value += villain_mass * terminal
            action_values.append(value)
        hero_br_value += hero_mass * max(action_values)
        profile_value += hero_mass * sum(
            probability * action_values[action_index]
            for action_index, probability in enumerate(hero_policy[hero_bucket])
        )

    # Hero value when the responder best-responds at each information set.
    villain_br_value = 0.0
    for villain_bucket, villain_mass in enumerate(spec.villain_prior):
        for action_index, action in enumerate(spec.actions):
            if spec.action_cost(action) is None:
                contribution = sum(
                    hero_mass
                    * hero_policy[hero_bucket][action_index]
                    * _payoff(spec, hero_bucket, villain_bucket, action_index)
                    for hero_bucket, hero_mass in enumerate(spec.hero_prior)
                )
            else:
                response_values = [
                    sum(
                        hero_mass
                        * hero_policy[hero_bucket][action_index]
                        * _payoff(
                            spec,
                            hero_bucket,
                            villain_bucket,
                            action_index,
                            response,
                        )
                        for hero_bucket, hero_mass in enumerate(spec.hero_prior)
                    )
                    for response in RESPONSES
                ]
                contribution = min(response_values)
            villain_br_value += villain_mass * contribution

    return max(0.0, hero_br_value - villain_br_value), profile_value


def solve_context(spec: ContextSpec, iterations: int) -> SolvedContext:
    """Solve one public game by exact-traversal vanilla CFR."""
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    strength_count = len(spec.strengths)
    action_count = len(spec.actions)
    hero_regrets = [[0.0] * action_count for _ in range(strength_count)]
    hero_sums = [[0.0] * action_count for _ in range(strength_count)]
    aggressive_indices = [
        index
        for index, action in enumerate(spec.actions)
        if spec.action_cost(action) is not None
    ]
    villain_regrets: Dict[Tuple[int, int], List[float]] = {
        (villain_bucket, action_index): [0.0, 0.0]
        for villain_bucket in range(strength_count)
        for action_index in aggressive_indices
    }
    villain_sums: Dict[Tuple[int, int], List[float]] = {
        key: [0.0, 0.0] for key in villain_regrets
    }

    initial_hero = [
        [1.0 / action_count for _ in range(action_count)]
        for _ in range(strength_count)
    ]
    initial_villain = {key: [0.5, 0.5] for key in villain_regrets}
    initial_gap, _ = _profile_gap(spec, initial_hero, initial_villain)

    for _ in range(iterations):
        hero_strategy = [_regret_matching(row) for row in hero_regrets]
        villain_strategy = {
            key: _regret_matching(row) for key, row in villain_regrets.items()
        }

        # Compute both players' updates from the same strategy profile.
        hero_deltas = [[0.0] * action_count for _ in range(strength_count)]
        for hero_bucket in range(strength_count):
            action_values: List[float] = []
            for action_index, action in enumerate(spec.actions):
                value = 0.0
                for villain_bucket, villain_mass in enumerate(spec.villain_prior):
                    if spec.action_cost(action) is None:
                        terminal = _payoff(
                            spec, hero_bucket, villain_bucket, action_index
                        )
                    else:
                        strategy = villain_strategy[(villain_bucket, action_index)]
                        terminal = sum(
                            strategy[response_index]
                            * _payoff(
                                spec,
                                hero_bucket,
                                villain_bucket,
                                action_index,
                                response,
                            )
                            for response_index, response in enumerate(RESPONSES)
                        )
                    value += villain_mass * terminal
                action_values.append(value)
            node_value = sum(
                probability * action_values[action_index]
                for action_index, probability in enumerate(hero_strategy[hero_bucket])
            )
            hero_deltas[hero_bucket] = [
                value - node_value for value in action_values
            ]

        villain_deltas: Dict[Tuple[int, int], List[float]] = {}
        for villain_bucket in range(strength_count):
            for action_index in aggressive_indices:
                response_values = []
                for response in RESPONSES:
                    # Counterfactual reach includes hero chance and action
                    # probability, but excludes the responder's own reach.
                    value = 0.0
                    for hero_bucket, hero_mass in enumerate(spec.hero_prior):
                        value += (
                            hero_mass
                            * hero_strategy[hero_bucket][action_index]
                            * -_payoff(
                                spec,
                                hero_bucket,
                                villain_bucket,
                                action_index,
                                response,
                            )
                        )
                    response_values.append(value)
                strategy = villain_strategy[(villain_bucket, action_index)]
                node_value = sum(
                    probability * response_values[response_index]
                    for response_index, probability in enumerate(strategy)
                )
                villain_deltas[(villain_bucket, action_index)] = [
                    value - node_value for value in response_values
                ]

        for hero_bucket in range(strength_count):
            for action_index in range(action_count):
                hero_regrets[hero_bucket][action_index] += hero_deltas[hero_bucket][
                    action_index
                ]
                hero_sums[hero_bucket][action_index] += hero_strategy[hero_bucket][
                    action_index
                ]
        for key, deltas in villain_deltas.items():
            for response_index in range(len(RESPONSES)):
                villain_regrets[key][response_index] += deltas[response_index]
                # Responder has no earlier choice, so own reach to each
                # information set is one in the behavioral average.
                villain_sums[key][response_index] += villain_strategy[key][
                    response_index
                ]

    hero_average = _average_rows(hero_sums)
    villain_average = {
        key: _average_rows([row])[0] for key, row in villain_sums.items()
    }
    final_gap, value = _profile_gap(spec, hero_average, villain_average)
    return SolvedContext(
        hero_average=hero_average,
        villain_average=villain_average,
        initial_gap=initial_gap,
        final_gap=final_gap,
        value=value,
    )


def _rounded_distribution(
    actions: Sequence[str], probabilities: Sequence[float]
) -> Dict[str, float]:
    rounded = [round(max(0.0, float(value)), PROBABILITY_DIGITS) for value in probabilities]
    difference = round(1.0 - sum(rounded), PROBABILITY_DIGITS)
    winner = max(range(len(rounded)), key=lambda index: rounded[index])
    rounded[winner] = round(rounded[winner] + difference, PROBABILITY_DIGITS)
    return {action: rounded[index] for index, action in enumerate(actions)}


def _context_config_digest(specs: Sequence[ContextSpec]) -> str:
    rows = []
    for spec in specs:
        rows.append(
            {
                "domain": spec.domain,
                "fields": spec.fields,
                "strengths": spec.strengths,
                "actions": spec.actions,
                "pot": spec.pot,
                "call_cost": spec.call_cost,
                "action_costs": spec.action_costs,
                "hero_prior": spec.hero_prior,
                "villain_prior": spec.villain_prior,
                "passive_realization": spec.passive_realization,
            }
        )
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def train_blueprint(
    iterations: int,
    *,
    specs: Optional[Sequence[ContextSpec]] = None,
) -> Dict[str, object]:
    """Train all requested contexts and return the serializable artifact."""
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    context_specs = list(specs) if specs is not None else build_context_specs()
    if not context_specs:
        raise ValueError("at least one context is required")

    policies: Dict[str, Dict[str, float]] = {}
    initial_gaps: List[float] = []
    final_gaps: List[float] = []
    values: List[float] = []
    mixed_rows = 0
    for spec in context_specs:
        solved = solve_context(spec, iterations)
        initial_gaps.append(solved.initial_gap)
        final_gaps.append(solved.final_gap)
        values.append(solved.value)
        for strength_index, strength in enumerate(spec.strengths):
            distribution = _rounded_distribution(
                spec.actions, solved.hero_average[strength_index]
            )
            policies[spec.row_key(strength)] = distribution
            meaningful = sum(
                probability >= MEANINGFUL_MIX_FLOOR
                for probability in distribution.values()
            )
            if meaningful >= 2:
                mixed_rows += 1

    trainer_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    loader_digest = hashlib.sha256(
        (ROOT / "src" / "blueprint_policy.py").read_bytes()
    ).hexdigest()
    public_contexts = len(context_specs)
    rows = len(policies)
    metadata: Dict[str, object] = {
        "policy_id": "abstract_full_tree_cfr_v1",
        "algorithm": "vanilla CFR; exact chance traversal; regret-matched average strategy",
        "requested_iters": iterations,
        "completed_iters": iterations,
        "iterations_are_per_public_context": True,
        "total_public_context_updates": iterations * public_contexts,
        "deterministic": True,
        "random_seed": None,
        "public_contexts": public_contexts,
        "policy_rows": rows,
        "meaningfully_mixed_rows": mixed_rows,
        "meaningful_probability_floor": MEANINGFUL_MIX_FLOOR,
        "private_strength_buckets_per_player": 5,
        "response_actions": list(RESPONSES),
        "probability_digits": PROBABILITY_DIGITS,
        "context_config_sha256": _context_config_digest(context_specs),
        "trainer_sha256": trainer_digest,
        "runtime_loader_sha256": loader_digest,
        "convergence": {
            "metric": "NashConv-style hero-BR minus responder-BR value",
            "mean_initial_gap": round(sum(initial_gaps) / public_contexts, 8),
            "mean_final_gap": round(sum(final_gaps) / public_contexts, 8),
            "max_final_gap": round(max(final_gaps), 8),
            "mean_profile_value": round(sum(values) / public_contexts, 8),
        },
        "scope": (
            "one representative responder per public context; five ordinal private "
            "strength buckets; one hero action and fold/call response after aggression"
        ),
        "limitations": [
            "not a solved six-player no-limit game",
            "no card-removal effects within strength buckets",
            "no continuation tree after a called aggression",
            "opponent priors and payoff abstraction are model assumptions",
        ],
        "reproduction_command": (
            f"python tools/train_blueprint.py --iterations {iterations} "
            f"--output data/{DEFAULT_ARTIFACT}"
        ),
        "wall_clock_timestamp_in_artifact": False,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": metadata,
        "policies": policies,
    }


def serialize_artifact(payload: Mapping[str, object]) -> bytes:
    """Canonical, byte-reproducible artifact serialization."""
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def write_artifact(payload: Mapping[str, object], output: Path) -> str:
    """Write policy plus sibling SHA-256 manifest and return the digest."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = serialize_artifact(payload)
    digest = hashlib.sha256(raw).hexdigest()
    output.write_bytes(raw)
    output.with_suffix(".sha256").write_text(
        f"{digest}  {output.name}\n", encoding="ascii"
    )
    return digest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=1200)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.iterations <= 0:
        parser.error("--iterations must be positive")

    payload = train_blueprint(args.iterations)
    digest = write_artifact(payload, args.output)
    metadata = payload["metadata"]
    convergence = metadata["convergence"]
    print(
        f"requested_iters={metadata['requested_iters']} "
        f"completed_iters={metadata['completed_iters']} "
        f"contexts={metadata['public_contexts']} rows={metadata['policy_rows']} "
        f"mixed_rows={metadata['meaningfully_mixed_rows']}"
    )
    print(
        f"mean_gap={convergence['mean_initial_gap']:.8f}"
        f"->{convergence['mean_final_gap']:.8f} "
        f"sha256={digest} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
