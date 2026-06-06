import zipfile

from tools import import_audit
from tools.edge_case_harness import (
    candidate_zip_paths,
    check_action_contract,
    scan_source_for_forbidden,
    validate_zip_structure,
)


def test_action_contract_rejects_expensive_raise_ambiguities():
    state = {
        "current_bet": 1000,
        "min_raise_to": 2200,
        "amount_owed": 900,
        "can_check": False,
        "your_stack": 5000,
        "your_bet_this_street": 100,
    }

    assert "raise_missing_amount" in check_action_contract({"action": "raise"}, state)
    assert any(issue.startswith("raise_below_min") for issue in check_action_contract({"action": "raise", "amount": 1500}, state))
    assert any(issue.startswith("raise_above_stack_cap") for issue in check_action_contract({"action": "raise", "amount": 99999}, state))
    assert any(issue.startswith("raise_equal_or_below_call") for issue in check_action_contract({"action": "raise", "amount": 1000}, state))
    assert check_action_contract({"action": "raise", "amount": 2200}, state) == []


def test_action_contract_rejects_check_when_call_required():
    state = {"amount_owed": 400, "can_check": False}
    assert check_action_contract({"action": "check"}, state) == ["check_facing_bet"]
    assert check_action_contract({"action": "fold"}, state) == []
    assert check_action_contract({"action": "call"}, state) == []


def test_import_audit_scans_canonical_src_clean():
    assert import_audit.scan_src() == []


def test_package_structure_and_forbidden_import_scan_for_candidate_zips():
    failures = []
    for spec in candidate_zip_paths(include_deployed=True):
        issues = validate_zip_structure(spec.path)
        if issues:
            failures.append(f"{spec.name}:{issues}")
    assert failures == []


def test_package_structure_validator_catches_bad_zip(tmp_path):
    bad_zip = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("bot.py", "import requests\n\ndef decide(state):\n    return {'action': 'fold'}\n")
        zf.writestr("extra.py", "print('bad root py')\n")
        zf.writestr("data/evil.py", "print('bad data py')\n")

    issues = validate_zip_structure(bad_zip)
    assert any("forbidden import requests" in issue for issue in issues)
    assert any(issue.startswith("unexpected_root_py") for issue in issues)
    assert "python_inside_data:data/evil.py" in issues


def test_forbidden_call_scanner_catches_dynamic_import_and_os_calls():
    issues = scan_source_for_forbidden(
        "import os\nx = __import__('math')\nos.system('true')\ny = globals()['x']\n",
        "fixture.py",
    )
    assert "fixture.py: forbidden call __import__(...)" in issues
    assert "fixture.py: forbidden call os.system(...)" in issues
    assert "fixture.py: forbidden call globals()[...]" in issues
