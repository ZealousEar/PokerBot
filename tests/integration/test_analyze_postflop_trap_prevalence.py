from pathlib import Path

from tools import analyze_postflop_trap_prevalence as extractor


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "postflop_trap_prevalence"


def test_postflop_trap_extractor_counts_required_synthetic_families():
    result = extractor.analyze_path(FIXTURE_DIR, top_n=20)

    assert result["total_records_found"] == 6
    assert result["records_successfully_parsed"] == 6
    assert result["postflop_action_records"] >= 8
    assert result["river_action_records"] >= 5

    clusters = {item["cluster_key"]: item for item in result["top_clusters_by_frequency"]}
    assert "river__button__raise__5card_unpaired_two_tone_static" in clusters
    assert "river__big_blind__fold__5card_paired_two_tone_static" in clusters

    can_check = result["river_can_check_raise_frequency"]
    assert can_check["unpaired_two_tone_static"]["raise"] >= 2
    assert can_check["wet_flush_draw"]["raise"] == 1

    facing = result["river_facing_bet_fold_call_frequency"]
    assert facing["paired_two_tone_static"]["fold"] == 1
    assert facing["unpaired_two_tone_static"]["call"] == 1

    fingerprints = result["action_sequence_fingerprints"]
    assert fingerprints["toby_river_can_check_unpaired_two_tone_static_raise_like"]["count"] >= 2
    assert fingerprints["toby_paired_board_river_facing_bet_fold_like"]["count"] == 1
    assert fingerprints["mehedi_preflop_pressure_early_bust_like"]["count"] == 1


def test_postflop_trap_extractor_reports_chip_impact_and_nonfinite_rejections():
    result = extractor.analyze_path(FIXTURE_DIR, top_n=20)

    assert result["chip_impact_available"] is True
    impact_keys = {item["cluster_key"] for item in result["top_clusters_by_chip_impact"]}
    assert "river__button__raise__5card_unpaired_two_tone_static" in impact_keys
    assert result["parse_quality"]["failures"]["nonfinite_amounts_rejected"] == 1
    assert "ROUNDS" in result["parse_quality"]["schema_keys"]["top_level_keys"]


def test_postflop_trap_extractor_handles_opaque_string_fixture_without_crashing():
    result = extractor.analyze_path(FIXTURE_DIR / "opaque_strings.json", top_n=5)

    assert result["total_records_found"] == 0
    assert result["records_successfully_parsed"] == 0
    assert result["postflop_action_records"] == 0
    assert result["river_action_records"] == 0
    assert result["top_clusters_by_frequency"] == []


def test_text_report_contains_required_summary_fields():
    result = extractor.analyze_path(FIXTURE_DIR, top_n=5)
    report = extractor.render_text_report(result)

    assert "Total records found: 6" in report
    assert "Postflop action records parsed:" in report
    assert "River can_check raise frequency" in report
    assert "Toby/Mehedi-like fingerprints" in report
