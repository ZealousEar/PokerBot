"""Standard preflop ranges by position and effective stack depth.

Format: `RANGES[position][stack_depth_bb] -> frozenset[str]` of canonical
hand strings (e.g. `"AKs"`, `"99"`, `"T9o"`).
"""
# TODO (G2): populate from a respected source. Cite via `# Source: ...`.
RANGES: dict = {}
