"""Contract test for the bounded exploit overlay.

The overlay in ``src/opponent_model.py`` deviates from the blueprint toward a
best response, but the deviation is *bounded*: no per-knob shift may leave the
band ``[-MAX_DEVIATION_PP, +MAX_DEVIATION_PP]`` (= ±0.20). That bound is the
whole safety argument for shipping the overlay, so it gets a property test.

There are two independent clip sites, and this file exercises both:

* **load-time** — ``_load_field_priors()`` clips the ``shift_by_cluster`` table
  as it is read from ``field_priors.npz`` (so a mistuned table cannot smuggle a
  large shift into memory);
* **emit-time** — ``OpponentModel.exploit_shift()`` clips again when it hands a
  shift to the strategy (defence in depth if the in-memory table is ever wrong).

We feed the module deliberately out-of-bound priors and assert the public
contract still holds. We are not testing ``numpy.clip`` itself — we are testing
that the module routes every emitted shift through a clip with the right bound.
"""
import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src import opponent_model as om
from src.opponent_model import MAX_DEVIATION_PP, SHIFT_KEYS, WARMUP_HANDS, OpponentModel

# float32 stores 0.20 as ~0.20000000298, so allow a hair of slack on the bound.
TOL = 1e-6
FEATURES = ("vpip", "pfr", "af", "fold_to_cbet")


@pytest.fixture(autouse=True)
def _restore_field_priors():
    """Snapshot and restore the module-level prior table around every test so
    nothing leaks into other suites (a clean clone has it as ``None``)."""
    saved = om._FIELD_PRIORS
    yield
    om._FIELD_PRIORS = saved


def _make_priors(shift_row):
    """A coherent one-cluster ``_FIELD_PRIORS`` dict whose shift row is whatever
    (possibly out-of-bound) values the caller supplies."""
    return {
        "feature_names": FEATURES,
        "cluster_names": ("c0",),
        "cluster_centroids": np.zeros((1, len(FEATURES)), dtype=np.float32),
        "cluster_scales": np.ones((len(FEATURES),), dtype=np.float32),
        "shift_by_cluster": np.asarray(shift_row, dtype=np.float32).reshape(1, len(SHIFT_KEYS)),
    }


def _warm_model(seat=1):
    model = OpponentModel()
    model._counts[seat]["hands"] = WARMUP_HANDS  # force past the warmup gate
    return model


def _assert_bounded(shifts):
    assert set(shifts.keys()) == set(SHIFT_KEYS)
    for key, value in shifts.items():
        assert -MAX_DEVIATION_PP - TOL <= value <= MAX_DEVIATION_PP + TOL, (key, value)


# --- emit-time clip: exploit_shift() -------------------------------------------------

@settings(max_examples=200, deadline=None)
@given(
    st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=len(SHIFT_KEYS),
        max_size=len(SHIFT_KEYS),
    )
)
def test_exploit_shift_stays_bounded_for_any_prior(shift_row):
    """For ANY finite prior row (in- or out-of-bound), a warm seat with a
    matching cluster gets a shift dict inside the ±0.20 band."""
    om._FIELD_PRIORS = _make_priors(shift_row)
    shifts = _warm_model(seat=1).exploit_shift(1)
    _assert_bounded(shifts)


def test_exploit_shift_clamps_extreme_prior_to_the_cap():
    """A wildly out-of-bound prior is pulled exactly to the cap, not passed
    through — proving the emit-time clip is load-bearing."""
    om._FIELD_PRIORS = _make_priors([+5.0, -5.0, +5.0, -5.0, +5.0, -5.0, +5.0])
    shifts = _warm_model(seat=1).exploit_shift(1)
    _assert_bounded(shifts)
    assert max(shifts.values()) == pytest.approx(MAX_DEVIATION_PP, abs=TOL)
    assert min(shifts.values()) == pytest.approx(-MAX_DEVIATION_PP, abs=TOL)


# --- load-time clip: _load_field_priors() ------------------------------------------

def test_load_field_priors_clips_the_shift_table(tmp_path, monkeypatch):
    """An out-of-bound shift table in the npz is clamped to ±0.20 at load time,
    so a large shift never even reaches memory."""
    shift = np.full((2, len(SHIFT_KEYS)), 5.0, dtype=np.float32)
    shift[1, :] = -5.0
    np.savez(
        tmp_path / "field_priors.npz",
        schema_version=np.array([1]),
        classifier_feature_names=np.array(list(FEATURES)),
        cluster_names=np.array(["c0", "c1"]),
        shift_names=np.array(list(SHIFT_KEYS)),
        cluster_centroids=np.zeros((2, len(FEATURES)), dtype=np.float32),
        cluster_scales=np.ones((len(FEATURES),), dtype=np.float32),
        shift_by_cluster=shift,
    )
    monkeypatch.setattr(om, "_data_dir", lambda: str(tmp_path))

    priors = om._load_field_priors()
    assert priors is not None, "synthetic in-schema npz should load"
    loaded = priors["shift_by_cluster"]
    assert np.all(loaded <= MAX_DEVIATION_PP + TOL)
    assert np.all(loaded >= -MAX_DEVIATION_PP - TOL)
    assert loaded.max() == pytest.approx(MAX_DEVIATION_PP, abs=TOL)
    assert loaded.min() == pytest.approx(-MAX_DEVIATION_PP, abs=TOL)


# --- neutral fallbacks (what a clean clone actually does) ---------------------------

def test_overlay_is_neutral_without_priors():
    """A clean clone has no field_priors.npz: even a warm seat gets all-zero
    shifts. This is the behaviour the notebook demonstrates."""
    om._FIELD_PRIORS = None
    shifts = _warm_model(seat=2).exploit_shift(2)
    assert shifts == {key: 0.0 for key in SHIFT_KEYS}


def test_overlay_is_neutral_before_warmup():
    """A cold seat (< WARMUP_HANDS observed) gets neutral shifts even when an
    out-of-bound prior table is loaded."""
    om._FIELD_PRIORS = _make_priors([5.0] * len(SHIFT_KEYS))
    shifts = OpponentModel().exploit_shift(3)  # seat 3 has zero observed hands
    assert shifts == {key: 0.0 for key in SHIFT_KEYS}
