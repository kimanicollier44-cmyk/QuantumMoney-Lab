"""Tests for QuantumMoney-Lab: qubit model, bank, forgery math, budget."""
import random
from fractions import Fraction

import pytest

import main as m


# ---- qubit model
def test_measure_matching_basis_faithful_and_non_disturbing():
    q = {"bit": 1, "basis": "+"}
    assert m.measure(q, "+", random.Random(1)) == 1
    assert q == {"bit": 1, "basis": "+"}


def test_measure_wrong_basis_replaces_state():
    q = {"bit": 0, "basis": "+"}
    out = m.measure(q, "×", random.Random(1))
    assert out in (0, 1)
    assert q["basis"] == "×" and q["bit"] == out


def test_bases():
    assert m.BASES == ("+", "×")


# ---- bank
def test_mint_records_match_note():
    bank = m.Bank()
    note = bank.mint("A-1", 16, random.Random(5))
    assert bank.records["A-1"] == [(q["bit"], q["basis"]) for q in note["qubits"]]


def test_mint_duplicate_serial_rejected():
    bank = m.Bank()
    bank.mint("A-1", 4, random.Random(5))
    with pytest.raises(ValueError):
        bank.mint("A-1", 4, random.Random(5))


def test_verify_unknown_serial_rejected():
    bank = m.Bank()
    with pytest.raises(KeyError):
        m.verify_note(bank, {"serial": "GHOST", "qubits": []}, random.Random(5))


def test_genuine_note_verifies_clean_and_repeatably():
    bank = m.Bank()
    note = bank.mint("A-1", 20, random.Random(5))
    rng = random.Random(6)
    assert m.verify_note(bank, note, rng)["errors"] == 0
    assert m.verify_note(bank, note, rng)["accepted"]


def test_same_seed_same_note_and_commitment():
    a, b = m.Bank(), m.Bank()
    na = a.mint("S", 20, random.Random(11))
    nb = b.mint("S", 20, random.Random(11))
    assert m.canonical_json(na) == m.canonical_json(nb)
    assert a.commitment() == b.commitment()


def test_tampered_record_changes_commitment_and_fails_note_once():
    bank = m.Bank()
    note = bank.mint("S", 20, random.Random(11))
    before = bank.commitment()
    bank.tamper_record("S", 0)
    assert bank.commitment() != before
    assert m.verify_note(bank, note, random.Random(3))["errors"] == 1


def test_genuine_simulation_all_pass():
    rep = m.simulate_genuine()
    assert rep["passed"] == rep["trials"] == 200


# ---- forgery math
def test_forger_qubit_pass_exact():
    assert m.forger_qubit_pass_probability() == Fraction(3, 4)


def test_counterfeit_acceptance_exact_fractions():
    assert m.counterfeit_acceptance(4) == Fraction(81, 256)
    assert m.counterfeit_acceptance(8) == Fraction(6561, 65536)


def test_counterfeit_acceptance_n16_decimal():
    assert abs(float(m.counterfeit_acceptance(16)) - 0.0100226) < 1e-6


def test_counterfeit_acceptance_strictly_decreasing():
    vals = [m.counterfeit_acceptance(n) for n in (4, 8, 16, 32, 64)]
    assert vals == sorted(vals, reverse=True)
    assert len(set(vals)) == len(vals)


def test_acceptance_table():
    table = m.acceptance_table()
    assert [row["n"] for row in table] == [4, 8, 16, 32, 64]
    assert table[0]["fraction"] == "81/256"
    assert abs(table[2]["decimal"] - 0.0100226) < 1e-6


def test_seeded_forgery_tracks_exact():
    sim = m.simulate_forgery()
    assert abs(sim["per_qubit"]["pass_rate"] - 0.75) < 0.02
    assert abs(sim["full_note"]["rate"] - sim["full_note"]["exact"]) < 0.03


# ---- error budget
def test_binomial_cdf_endpoints():
    assert m.binomial_cdf(20, Fraction(1, 50), 20) == 1
    assert m.binomial_cdf(20, Fraction(1, 50), 0) == Fraction(49, 50) ** 20


def test_forger_mismatch_probability():
    assert m.forger_mismatch_probability(Fraction(0)) == Fraction(1, 4)
    assert m.forger_mismatch_probability(m.DEMO_EPSILON) == Fraction(13, 50)


def test_budget_separation():
    g = m.genuine_acceptance(m.DEMO_QUBITS, m.DEMO_EPSILON, m.DEMO_TOLERANCE)
    f = m.forger_acceptance(m.DEMO_QUBITS, m.DEMO_EPSILON, m.DEMO_TOLERANCE)
    assert g > Fraction(99, 100)
    assert f < Fraction(8, 100)
    assert g > 10 * f


def test_acceptance_threshold():
    assert m.acceptance_threshold(m.DEMO_QUBITS, m.DEMO_EPSILON) == 3


def test_error_budget_report_consistent():
    budget = m.error_budget()
    assert budget["n"] == m.DEMO_QUBITS
    assert budget["genuine_acceptance"] == float(
        m.genuine_acceptance(m.DEMO_QUBITS, m.DEMO_EPSILON, m.DEMO_TOLERANCE))


# ---- oracle problem + demo book
def test_merchant_self_check_disturbs_and_dooms_note():
    book = m.build_demo_book()
    assert book["merchant_damage"]["disturbed"] >= 1
    rep = m.demo_book_reports()
    assert rep["merchant_checked_QM-0002"]["errors"] >= 1
    assert not rep["merchant_checked_QM-0002"]["accepted"]


def test_demo_book_outcomes():
    rep = m.demo_book_reports()
    assert rep["genuine_QM-0001"]["accepted"]
    assert rep["genuine_QM-0001"]["errors"] == 0
    assert not rep["forged_QM-0001"]["accepted"]
    assert rep["forged_QM-0001"]["errors"] >= 1
    assert rep["tampered_record_QM-0003"]["errors"] == 1
    assert rep["commitment_changed_by_tamper"]


# ---- labelled notes
def test_cloning_bound_labelled():
    assert m.CLONING_BOUND["value"] == "5/6"
    assert m.CLONING_BOUND["status"] == "LABELLED"
    assert m.CLONING_BOUND["derived_here"] is False


def test_public_key_note_labelled_not_built():
    assert m.PUBLIC_KEY_MONEY_NOTE["built_here"] is False
    assert "open" in m.PUBLIC_KEY_MONEY_NOTE["status"]


# ---- classifier
def test_classifier_scenarios():
    rep = m.classifier_report()
    assert rep["clean_note_0_errors"] == "genuine"
    assert rep["one_error_noisy_channel"] == "genuine"
    assert rep["borderline_3_errors"] == "suspect"
    assert rep["quarter_errors_classic_forgery"] == "forged"
    assert rep["eight_qubit_note_clean"] == "genuine"
    assert rep["large_note_quarter_errors"] == "forged"
    assert rep["large_note_light_noise"] == "genuine"
    assert rep["large_note_mid_errors"] == "suspect"


def test_classifier_matches_model_on_scenarios():
    for features in [(0, 20, 0.02), (1, 20, 0.02), (3, 20, 0.02),
                     (5, 20, 0.02), (0, 8, 0.0), (8, 32, 0.0),
                     (2, 32, 0.05), (6, 32, 0.05)]:
        assert m.classify_note(*features) == m.model_label(*features)


# ---- gates + seats
def test_hold_gates_14_all_hold():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_gate_outcomes():
    assert m.gate("real_currency_issuance") == "HOLD"
    assert m.gate("payment_system_use") == "HOLD"
    assert m.gate("toy_math_as_security_proof_claim") == "HOLD"
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    brains = m.brains_report()
    assert brains["decider"]["can_override_hold"] is False
    assert brains["decider"]["seat"] == "Gemini Argon 4 Extended Thinking"
    assert brains["advisor"]["can_override_hold"] is False
    assert brains["flow"]["rendered"] is False
    assert brains["flow"]["live"] == 0


def test_hold_demo_exits_2():
    assert m.main(["hold-demo"]) == 2
    assert m.main(["hold-demo", "payment_system_use"]) == 2
    assert m.main(["hold-demo", "run_simulation"]) == 0


def test_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks)
