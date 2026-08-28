"""Runtime loader and abstraction helpers for the trained mixed blueprint.

The artifact is generated offline by :mod:`tools.train_blueprint`.  Runtime
code only validates a small JSON table and performs exact-key lookups; it does
not train, import development dependencies, or execute dynamic code.

The policy intentionally returns *distributions*.  Callers can either use the
mode with :func:`most_likely` or supply a deterministic draw in ``[0, 1)`` to
:func:`sample_action`.  Supplying the draw keeps random-state ownership with
the bot/engine and makes replayed hands reproducible.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Mapping, Optional


SCHEMA_VERSION = 1
DEFAULT_ARTIFACT = "blueprint_policy_v1.json"

PREFLOP_POSITIONS = ("UTG", "MP", "CO", "BTN", "SB", "BB")
PREFLOP_PRESSURES = ("unopened", "limped", "open", "threebet", "fourbet")
POSTFLOP_STREETS = ("flop", "turn", "river")
POSTFLOP_TEXTURES = ("dry", "wet", "paired", "monotone")
POSTFLOP_PRESSURES = ("free", "small", "medium", "large")
STACK_BUCKETS = ("short", "medium", "deep")
PREFLOP_STRENGTHS = ("trash", "weak", "medium", "strong", "premium")
POSTFLOP_STRENGTHS = ("air", "draw", "marginal", "strong", "nuts")


class BlueprintPolicyError(ValueError):
    """Raised when an artifact or lookup request violates the policy schema."""


def _choice(value: str, choices: tuple[str, ...], label: str) -> str:
    normalized = str(value).strip().lower()
    by_lower = {item.lower(): item for item in choices}
    if normalized not in by_lower:
        raise BlueprintPolicyError(
            f"unknown {label} {value!r}; expected one of {', '.join(choices)}"
        )
    return by_lower[normalized]


def preflop_stack_bucket(effective_stack_bb: float) -> str:
    """Map effective stack depth to the three training buckets."""
    value = float(effective_stack_bb)
    if not math.isfinite(value) or value < 0:
        raise BlueprintPolicyError("effective_stack_bb must be finite and non-negative")
    if value <= 20.0:
        return "short"
    if value <= 80.0:
        return "medium"
    return "deep"


def postflop_stack_bucket(spr: float) -> str:
    """Map stack-to-pot ratio to the three training buckets."""
    value = float(spr)
    if not math.isfinite(value) or value < 0:
        raise BlueprintPolicyError("spr must be finite and non-negative")
    if value <= 2.0:
        return "short"
    if value <= 6.0:
        return "medium"
    return "deep"


def preflop_strength_bucket(hand: str) -> str:
    """Map a canonical preflop tag (``AA``, ``AKs``, ``QJo``) to five buckets.

    The mapping is deliberately compact because the trained game solves five
    private-strength classes rather than all 169 starting hands.  It is a
    stable integration boundary, not a claim that hands within a bucket are
    strategically identical.
    """
    raw = str(hand).strip()
    if len(raw) not in (2, 3):
        raise BlueprintPolicyError(f"invalid canonical hand {hand!r}")
    rank_order = "23456789TJQKA"
    first, second = raw[0].upper(), raw[1].upper()
    if first not in rank_order or second not in rank_order:
        raise BlueprintPolicyError(f"invalid canonical hand {hand!r}")

    if first == second:
        if len(raw) != 2:
            raise BlueprintPolicyError(f"pairs must omit suitedness: {hand!r}")
        if first in "AKQ":
            return "premium"
        if first in "JT":
            return "strong"
        if first in "9876":
            return "medium"
        return "weak"

    if len(raw) != 3 or raw[2].lower() not in ("s", "o"):
        raise BlueprintPolicyError(f"unpaired hands require s/o suffix: {hand!r}")
    suited = raw[2].lower() == "s"
    high, low = sorted(
        (rank_order.index(first), rank_order.index(second)), reverse=True
    )
    high_rank, low_rank = rank_order[high], rank_order[low]
    gap = high - low

    if suited and high_rank == "A" and low_rank == "K":
        return "premium"
    if (high_rank == "A" and low_rank in "KQ") or (
        suited and (high_rank, low_rank) in {("A", "J"), ("K", "Q")}
    ):
        return "strong"
    if suited and (
        high_rank == "A"
        or (high >= rank_order.index("9") and gap <= 2)
        or (high_rank, low_rank) in {("K", "J"), ("K", "T"), ("Q", "J")}
    ):
        return "medium"
    if not suited and (
        (high_rank == "A" and low_rank in "JT9")
        or (high_rank, low_rank) in {("K", "Q"), ("K", "J"), ("Q", "J")}
    ):
        return "medium"
    if suited and gap <= 3 and high >= rank_order.index("6"):
        return "weak"
    if high_rank == "A" or (suited and high >= rank_order.index("T")):
        return "weak"
    return "trash"


def postflop_strength_bucket(
    equity: float, *, has_draw: bool = False, is_nutted: bool = False
) -> str:
    """Map equity plus cheap structural flags to five postflop buckets."""
    value = float(equity)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise BlueprintPolicyError("equity must be finite and in [0, 1]")
    if is_nutted or value >= 0.88:
        return "nuts"
    if value >= 0.70:
        return "strong"
    if has_draw and value < 0.62:
        return "draw"
    if value >= 0.42:
        return "marginal"
    if has_draw:
        return "draw"
    return "air"


def preflop_context_key(
    position: str, pressure: str, stack: str, strength: str
) -> str:
    position_value = _choice(position, PREFLOP_POSITIONS, "position")
    pressure_aliases = {
        "none": "unopened",
        "first_in": "unopened",
        "raise": "open",
        "3bet": "threebet",
        "3-bet": "threebet",
        "4bet": "fourbet",
        "4-bet": "fourbet",
    }
    pressure_value = pressure_aliases.get(str(pressure).strip().lower(), pressure)
    pressure_value = _choice(pressure_value, PREFLOP_PRESSURES, "preflop pressure")
    stack_value = _choice(stack, STACK_BUCKETS, "stack bucket")
    strength_value = _choice(strength, PREFLOP_STRENGTHS, "preflop strength")
    return (
        f"preflop|position={position_value}|pressure={pressure_value}"
        f"|stack={stack_value}|strength={strength_value}"
    )


def postflop_context_key(
    street: str, texture: str, pressure: str, stack: str, strength: str
) -> str:
    street_value = _choice(street, POSTFLOP_STREETS, "street")
    texture_value = _choice(texture, POSTFLOP_TEXTURES, "texture")
    pressure_aliases = {"none": "free", "check": "free", "checked": "free"}
    pressure_value = pressure_aliases.get(str(pressure).strip().lower(), pressure)
    pressure_value = _choice(pressure_value, POSTFLOP_PRESSURES, "postflop pressure")
    stack_value = _choice(stack, STACK_BUCKETS, "stack bucket")
    strength_value = _choice(strength, POSTFLOP_STRENGTHS, "postflop strength")
    return (
        f"postflop|street={street_value}|texture={texture_value}"
        f"|pressure={pressure_value}|stack={stack_value}|strength={strength_value}"
    )


def _digest_path(path: Path) -> Path:
    return path.with_suffix(".sha256")


class BlueprintPolicy:
    """Validated immutable-style access to an offline-trained lookup table."""

    def __init__(
        self,
        policies: Mapping[str, Mapping[str, float]],
        metadata: Mapping[str, object],
        source_path: Optional[Path] = None,
    ) -> None:
        self._policies: Dict[str, Dict[str, float]] = {
            key: dict(distribution) for key, distribution in policies.items()
        }
        self.metadata = dict(metadata)
        self.source_path = source_path
        self._validate()

    @classmethod
    def load(
        cls, path: Optional[Path] = None, *, verify_digest: bool = True
    ) -> "BlueprintPolicy":
        artifact = (
            Path(path)
            if path is not None
            else Path(__file__).resolve().parent.parent / "data" / DEFAULT_ARTIFACT
        )
        raw = artifact.read_bytes()
        if verify_digest:
            digest_file = _digest_path(artifact)
            try:
                expected = digest_file.read_text(encoding="ascii").split()[0]
            except (FileNotFoundError, IndexError) as exc:
                raise BlueprintPolicyError(
                    f"missing or empty blueprint digest file: {digest_file}"
                ) from exc
            actual = hashlib.sha256(raw).hexdigest()
            if actual != expected:
                raise BlueprintPolicyError(
                    f"blueprint digest mismatch: expected {expected}, got {actual}"
                )
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BlueprintPolicyError(f"invalid blueprint JSON: {artifact}") from exc
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise BlueprintPolicyError(
                f"unsupported blueprint schema {payload.get('schema_version')!r}"
            )
        return cls(payload.get("policies", {}), payload.get("metadata", {}), artifact)

    def _validate(self) -> None:
        requested = self.metadata.get("requested_iters")
        completed = self.metadata.get("completed_iters")
        if not isinstance(requested, int) or requested <= 0:
            raise BlueprintPolicyError("metadata requested_iters must be a positive integer")
        if not isinstance(completed, int) or completed <= 0:
            raise BlueprintPolicyError("metadata completed_iters must be a positive integer")
        if completed > requested:
            raise BlueprintPolicyError("completed_iters cannot exceed requested_iters")
        if not self._policies:
            raise BlueprintPolicyError("blueprint contains no policy rows")
        for key, distribution in self._policies.items():
            if not distribution:
                raise BlueprintPolicyError(f"empty action distribution for {key}")
            total = 0.0
            for action, probability in distribution.items():
                if not action:
                    raise BlueprintPolicyError(f"empty action label for {key}")
                if not isinstance(probability, (int, float)):
                    raise BlueprintPolicyError(f"non-numeric probability for {key}/{action}")
                value = float(probability)
                if not math.isfinite(value) or value < 0.0 or value > 1.0:
                    raise BlueprintPolicyError(f"invalid probability for {key}/{action}")
                total += value
            if abs(total - 1.0) > 1e-6:
                raise BlueprintPolicyError(
                    f"probabilities for {key} sum to {total:.12f}, not 1"
                )

    def __len__(self) -> int:
        return len(self._policies)

    def distribution(self, context_key: str) -> Dict[str, float]:
        """Return a defensive copy of one action distribution."""
        try:
            return dict(self._policies[context_key])
        except KeyError as exc:
            raise BlueprintPolicyError(f"context is absent from blueprint: {context_key}") from exc

    def preflop_distribution(
        self,
        position: str,
        hand: str,
        *,
        pressure: str = "unopened",
        effective_stack_bb: float = 100.0,
    ) -> Dict[str, float]:
        key = preflop_context_key(
            position,
            pressure,
            preflop_stack_bucket(effective_stack_bb),
            preflop_strength_bucket(hand),
        )
        return self.distribution(key)

    def postflop_distribution(
        self,
        street: str,
        equity: float,
        *,
        texture: str = "dry",
        pressure: str = "free",
        spr: float = 8.0,
        has_draw: bool = False,
        is_nutted: bool = False,
    ) -> Dict[str, float]:
        key = postflop_context_key(
            street,
            texture,
            pressure,
            postflop_stack_bucket(spr),
            postflop_strength_bucket(equity, has_draw=has_draw, is_nutted=is_nutted),
        )
        return self.distribution(key)


def most_likely(distribution: Mapping[str, float]) -> str:
    """Return the modal action, resolving exact ties lexicographically."""
    if not distribution:
        raise BlueprintPolicyError("cannot select from an empty distribution")
    return min(distribution, key=lambda action: (-float(distribution[action]), action))


def sample_action(distribution: Mapping[str, float], draw: float) -> str:
    """Sample stably from ``distribution`` using a caller-provided draw.

    Actions are accumulated lexicographically so JSON key order and Python
    implementation details cannot change replay results.
    """
    value = float(draw)
    if not math.isfinite(value) or not 0.0 <= value < 1.0:
        raise BlueprintPolicyError("draw must be finite and in [0, 1)")
    if not distribution:
        raise BlueprintPolicyError("cannot sample from an empty distribution")
    ordered = []
    total = 0.0
    for action in sorted(distribution):
        probability = float(distribution[action])
        if not math.isfinite(probability) or probability < 0.0 or probability > 1.0:
            raise BlueprintPolicyError(f"invalid probability for action {action!r}")
        ordered.append((action, probability))
        total += probability
    if abs(total - 1.0) > 1e-6:
        raise BlueprintPolicyError(f"distribution sums to {total:.12f}, not 1")

    cumulative = 0.0
    last = ""
    for action, probability in ordered:
        cumulative += probability
        last = action
        if value < cumulative:
            return action
    if last:
        return last
    raise BlueprintPolicyError("cannot sample from an empty distribution")


__all__ = [
    "BlueprintPolicy",
    "BlueprintPolicyError",
    "most_likely",
    "postflop_context_key",
    "postflop_stack_bucket",
    "postflop_strength_bucket",
    "preflop_context_key",
    "preflop_stack_bucket",
    "preflop_strength_bucket",
    "sample_action",
]
