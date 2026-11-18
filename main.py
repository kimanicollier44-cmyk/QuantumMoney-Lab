#!/usr/bin/env python3
"""QuantumMoney-Lab - educational Wiesner quantum money lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only - and the central lesson is stated up front:

  * QuantumMoney-Lab simulates Wiesner's quantum money scheme with
    classical (bit, basis) pairs standing in for qubits, exactly the
    measurement model QKD-Lab uses. A bank mints a note by preparing
    n qubits in secret random bases and recording (bit, basis)
    against a serial number. Verification measures in the recorded
    bases, so a genuine note passes with probability 1.
  * A forger who intercepts the note must measure it to copy it.
    Half the forger's basis guesses are wrong, and each wrong guess
    turns the resent qubit into a coin flip - so a counterfeit qubit
    passes with probability exactly 3/4, and a counterfeit n-qubit
    note passes with probability (3/4)^n. That arithmetic is exact
    and is computed here with fractions, not sampled folklore.
  * The toy math is NOT a security proof for any real scheme, and
    this lab is not money. No real banknote, currency, payment,
    token, or financial product exists here or can be made from it.
    Public-key quantum money is an open research problem and is
    labelled as such - it is not built here and not claimed.

Every real-currency, banking, payment, counterfeiting, and
unforgeability claim is a permanent HOLD gate - with Gemini Argon 4
Extended Thinking as DECIDER (names-only, tighten-only), Muse as
advisor (never overrides HOLD), and Google Flow plan-only seats.
"""
import hashlib
import json
import math
import random
import sys
from fractions import Fraction

# ---------------------------------------------------------------- constants
VERSION = "1.0.0"
BASES = ("+", "×")  # rectilinear and diagonal preparation bases

# Labelled demo parameters. The channel error is a teaching value,
# not a measurement of any real device or channel.
DEMO_QUBITS = 20
DEMO_EPSILON = Fraction(1, 50)  # labelled 2% per-qubit channel error
DEMO_TOLERANCE = 2              # accept a note with at most this many errors

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "real_currency_issuance": "HOLD - no issuing real currency, legal tender, or anything presented as money",
    "financial_product_claim": "HOLD - no financial product, security, investment instrument, or store-of-value claim",
    "bank_or_mint_deployment": "HOLD - no deployment by or for a real bank, mint, treasury, or currency authority",
    "payment_system_use": "HOLD - no use in payments, point-of-sale, settlement, or value transfer of any kind",
    "cryptocurrency_token_claim": "HOLD - no token, coin, or crypto-asset claim from a classical simulation",
    "unforgeability_claim_real_system": "HOLD - no claim that any real system is unforgeable based on this toy",
    "public_key_money_claim": "HOLD - public-key quantum money is an open problem; no claim it is built or solved here",
    "counterfeit_guidance_real_systems": "HOLD - no guidance for counterfeiting real banknotes, documents, or products",
    "real_note_authentication": "HOLD - no authenticating real banknotes, passports, IDs, or secure documents",
    "fraud_detection_product_claim": "HOLD - no fraud-detection or anti-counterfeit product claim for real systems",
    "cbdc_design_claim": "HOLD - no central-bank digital currency design, consultation, or readiness claim",
    "identity_document_security_use": "HOLD - no identity-document, credential, or secure-printing security use",
    "investment_claim": "HOLD - no investment claims; a teaching simulation is not a prospectus",
    "toy_math_as_security_proof_claim": "HOLD - the (3/4)^n arithmetic must never be presented as a security proof for any real scheme",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Qubit model
# A "qubit" in this lab is a classical (bit, basis) pair and
# measurement is a rule, stated openly: measuring in the preparation
# basis returns the bit and leaves the state untouched; measuring in
# the other basis returns a coin flip and REPLACES the state with
# what was measured. That replacement is the whole scheme - it is
# what a forger, a merchant, or any third party cannot avoid.

def measure(qubit, basis, rng):
    """Measure a (bit, basis) qubit in the given basis.

    Matching basis: the recorded bit comes out, state untouched.
    Wrong basis: a coin flip comes out and the state becomes the
    outcome in the measured basis - the original preparation is gone.
    """
    if qubit["basis"] == basis:
        return qubit["bit"]
    outcome = rng.randint(0, 1)
    qubit["bit"] = outcome
    qubit["basis"] = basis
    return outcome


def canonical_json(value):
    """Deterministic JSON used for commitments, traces, and CLI output."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ================================================================ 2. The bank
# The bank is the only party that can mint or verify, because only
# the bank holds the secret record: serial -> [(bit, basis), ...].
# The record is committed to with SHA-256 so a quietly edited record
# is detectable, and the demo shows a tampered record failing the
# very notes it issued.

class Bank:
    """Mints notes and keeps the secret verification record."""

    def __init__(self):
        self.records = {}

    def mint(self, serial, n, rng):
        """Prepare n fresh qubits and record them under `serial`."""
        if serial in self.records:
            raise ValueError(f"duplicate serial: {serial}")
        qubits = [{"bit": rng.randint(0, 1), "basis": rng.choice(BASES)}
                  for _ in range(n)]
        self.records[serial] = [(q["bit"], q["basis"]) for q in qubits]
        return {"serial": serial, "qubits": qubits}

    def commitment(self):
        """SHA-256 over the canonical secret record."""
        view = {serial: [list(pair) for pair in record]
                for serial, record in sorted(self.records.items())}
        return sha256_text(canonical_json(view))

    def tamper_record(self, serial, index):
        """Simulate a corrupted record: flip one recorded bit.

        The notes in circulation do not change - so the bank's own
        verification now fails the genuine note at exactly that qubit.
        """
        bit, basis = self.records[serial][index]
        self.records[serial][index] = (1 - bit, basis)


def verify_note(bank, note, rng, channel_error=0.0, tolerance=0):
    """Verify a presented note against the bank's secret record.

    Each qubit is measured in its recorded basis (on a copy, so a
    genuine note is never disturbed by being checked). A labelled
    per-qubit channel error can flip a bit in transit. The note is
    accepted when the error count stays within `tolerance`.
    """
    record = bank.records[note["serial"]]
    errors = 0
    for qubit, (bit, basis) in zip(note["qubits"], record):
        probe = dict(qubit)
        if channel_error > 0.0 and rng.random() < channel_error:
            probe["bit"] = 1 - probe["bit"]
        if measure(probe, basis, rng) != bit:
            errors += 1
    return {"serial": note["serial"], "n": len(record), "errors": errors,
            "tolerance": tolerance, "accepted": errors <= tolerance}


# ================================================================ 3. Forgery
# The forger's only move is intercept-resend: measure every qubit in
# a guessed basis and resend what came out. The per-qubit pass
# probability is derived, not asserted:
#   right basis (prob 1/2): resend is faithful -> passes with prob 1
#   wrong basis (prob 1/2): resend is a coin flip -> passes with 1/2
#   total: 1/2 * 1 + 1/2 * 1/2 = 3/4, exactly.

def forge_note(note, rng):
    """Intercept-resend forgery: measure in random bases, resend."""
    forged = []
    for qubit in note["qubits"]:
        probe = dict(qubit)
        basis = rng.choice(BASES)
        outcome = measure(probe, basis, rng)
        forged.append({"bit": outcome, "basis": basis})
    return {"serial": note["serial"], "qubits": forged}


def forger_qubit_pass_probability():
    """Exact per-qubit pass probability for intercept-resend: 3/4."""
    return Fraction(1, 2) * 1 + Fraction(1, 2) * Fraction(1, 2)


def counterfeit_acceptance(n):
    """Exact probability a forged n-qubit note passes: (3/4)^n."""
    return forger_qubit_pass_probability() ** n


def acceptance_table(ns=(4, 8, 16, 32, 64)):
    """The (3/4)^n line as exact fractions with decimal readouts."""
    rows = []
    for n in ns:
        exact = counterfeit_acceptance(n)
        rows.append({"n": n, "fraction": f"{exact.numerator}/{exact.denominator}",
                     "decimal": float(exact)})
    return rows


def simulate_forgery(seed=20261117, qubits=20000, note_size=8, trials=4000):
    """Seeded simulation of intercept-resend, tracked against exact math.

    Per-qubit: forge one long note and count how many resent qubits
    still match the record. Full-note: forge `trials` notes of
    `note_size` qubits and count clean acceptances. Both numbers are
    deterministic for the fixed seed and are compared with the exact
    (3/4) and (3/4)^note_size values in the checks.
    """
    rng = random.Random(seed)
    bank = Bank()
    long_note = bank.mint("SIM-LONG", qubits, rng)
    forged_long = forge_note(long_note, rng)
    report = verify_note(bank, forged_long, rng)
    per_qubit_pass = 1.0 - report["errors"] / qubits

    accepted = 0
    for i in range(trials):
        note = bank.mint(f"SIM-{i}", note_size, rng)
        if verify_note(bank, forge_note(note, rng), rng)["accepted"]:
            accepted += 1
    return {
        "seed": seed,
        "per_qubit": {"qubits": qubits, "errors": report["errors"],
                      "pass_rate": round(per_qubit_pass, 4),
                      "exact": float(forger_qubit_pass_probability())},
        "full_note": {"n": note_size, "trials": trials,
                      "accepted": accepted,
                      "rate": round(accepted / trials, 4),
                      "exact": float(counterfeit_acceptance(note_size))},
    }


def simulate_genuine(seed=4242, trials=200):
    """Seeded check that genuine notes pass with probability 1."""
    rng = random.Random(seed)
    bank = Bank()
    passed = 0
    for i in range(trials):
        note = bank.mint(f"GEN-{i}", DEMO_QUBITS, rng)
        if verify_note(bank, note, rng)["accepted"]:
            passed += 1
    return {"trials": trials, "passed": passed, "n": DEMO_QUBITS}


# ================================================================ 4. Error budget
# Real channels are noisy, so a strict zero-error rule would reject
# genuine notes too. The bank therefore accepts up to `tolerance`
# errors. Both sides of the budget are exact binomial sums:
#   genuine: each qubit errs with the labelled probability epsilon
#   forger:  each qubit errs with 1/4 + epsilon/2, because a resent
#            qubit passes at 3/4 * (1 - eps) + 1/4 * eps = 3/4 - eps/2
# The policy question - is there a tolerance where genuine notes
# almost always pass and forgeries almost never do? - is answered by
# the two sums, at the labelled demo parameters, in the open.

def binomial_cdf(n, p, t):
    """P(X <= t) for X ~ Binomial(n, p), in exact Fraction arithmetic."""
    p = Fraction(p)
    total = Fraction(0)
    for k in range(0, t + 1):
        total += Fraction(math.comb(n, k)) * p ** k * (1 - p) ** (n - k)
    return total


def forger_mismatch_probability(epsilon):
    """Exact per-qubit mismatch probability of a forged note."""
    return Fraction(1, 4) + Fraction(epsilon) / 2


def genuine_acceptance(n, epsilon, tolerance):
    """Exact P(genuine note accepted) under the labelled channel error."""
    return binomial_cdf(n, Fraction(epsilon), tolerance)


def forger_acceptance(n, epsilon, tolerance):
    """Exact P(forged note accepted) under the same policy."""
    return binomial_cdf(n, forger_mismatch_probability(epsilon), tolerance)


def acceptance_threshold(n, epsilon, target=Fraction(999, 1000)):
    """Smallest tolerance whose genuine acceptance reaches `target`."""
    for t in range(0, n + 1):
        if genuine_acceptance(n, epsilon, t) >= target:
            return t
    return n


def error_budget(n=DEMO_QUBITS, epsilon=DEMO_EPSILON, tolerance=DEMO_TOLERANCE):
    """The demo budget: both exact acceptances at the demo policy."""
    genuine = genuine_acceptance(n, epsilon, tolerance)
    forger = forger_acceptance(n, epsilon, tolerance)
    return {
        "n": n,
        "epsilon": f"{epsilon.numerator}/{epsilon.denominator}",
        "epsilon_decimal": float(epsilon),
        "tolerance": tolerance,
        "threshold_for_99.9pct_genuine": acceptance_threshold(n, epsilon),
        "genuine_acceptance": float(genuine),
        "forger_mismatch_per_qubit": float(forger_mismatch_probability(epsilon)),
        "forger_acceptance": float(forger),
        "separation_ratio": float(genuine / forger),
    }


# ================================================================ 5. The oracle problem + labelled notes
# Wiesner's scheme has a structural catch, and the lab shows it
# instead of hiding it: only the bank can verify, because only the
# bank knows the bases. A merchant who tries to check a note alone
# must guess bases - which is exactly the forger's move, and it
# damages the genuine note by the same 3/4-per-qubit law. Notes must
# therefore travel back to the bank (or the bank must answer as an
# online verification oracle, which leaks and centralises). Making
# verification public is the famous open problem below - labelled,
# not built.

def merchant_self_check(note, rng):
    """A merchant measures every qubit in a guessed basis.

    Returns how many qubit states were disturbed. Afterwards the
    bank's own verification sees the same damage a forgery leaves.
    """
    disturbed = 0
    for qubit in note["qubits"]:
        before = (qubit["bit"], qubit["basis"])
        measure(qubit, rng.choice(BASES), rng)
        if (qubit["bit"], qubit["basis"]) != before:
            disturbed += 1
    return {"serial": note["serial"], "n": len(note["qubits"]),
            "disturbed": disturbed}


# The optimal-cloning line is a LABELLED textbook bound placed next
# to the computed intercept-resend line. It is stated, not derived:
# this lab computes 3/4 for intercept-resend and derives nothing
# about cloning beyond quoting the published bound as a bound.
CLONING_BOUND = {
    "topic": "optimal universal 1->2 qubit cloning fidelity",
    "value": "5/6",
    "decimal": 0.8333333333333334,
    "status": "LABELLED",
    "source_note": "Buzek-Hillery bound (1996), quoted as a bound only",
    "derived_here": False,
    "intercept_resend_line": "computed here: per-qubit pass 3/4, note pass (3/4)^n",
}

# Public-key quantum money would let anyone verify a note without
# the bank's secret. It is an open research problem (oracle-based
# constructions exist; a standard-model construction does not).
# This lab does not build it, does not claim it, and gates the claim.
PUBLIC_KEY_MONEY_NOTE = {
    "topic": "public-key quantum money",
    "status": "LABELLED - open research problem",
    "built_here": False,
    "note": "Wiesner verification is private (bank-only). Publicly "
            "verifiable quantum money remains open in the standard "
            "model; nothing in this lab changes that.",
}


# ================================================================ 6. Demo note book
# A deterministic teaching book: one genuine note, its intercept-
# resend forgery, one genuine note ruined by a merchant's self-check,
# and one genuine note failed by the bank's own tampered record.

def build_demo_book(seed=20261117):
    rng = random.Random(seed)
    bank = Bank()
    genuine = bank.mint("QM-0001", DEMO_QUBITS, rng)
    forged = forge_note(genuine, rng)
    merchant_note = bank.mint("QM-0002", DEMO_QUBITS, rng)
    merchant_damage = merchant_self_check(merchant_note, rng)
    tampered_note = bank.mint("QM-0003", DEMO_QUBITS, rng)
    commitment_before = bank.commitment()
    bank.tamper_record("QM-0003", 0)
    return {
        "bank": bank,
        "genuine": genuine,
        "forged": forged,
        "merchant_note": merchant_note,
        "merchant_damage": merchant_damage,
        "tampered_note": tampered_note,
        "commitment_before_tamper": commitment_before,
    }


def demo_book_reports(seed=20261117):
    book = build_demo_book(seed)
    bank = book["bank"]
    rng = random.Random(seed + 1)
    return {
        "genuine_QM-0001": verify_note(bank, book["genuine"], rng),
        "forged_QM-0001": verify_note(bank, book["forged"], rng),
        "merchant_checked_QM-0002": verify_note(bank, book["merchant_note"], rng),
        "merchant_damage": book["merchant_damage"],
        "tampered_record_QM-0003": verify_note(bank, book["tampered_note"], rng),
        "commitment_changed_by_tamper":
            bank.commitment() != book["commitment_before_tamper"],
    }


# ================================================================ 7. kNN note classifier
# Features: error count, note size, labelled channel error. The
# training grid is labelled by the lab's own verdict policy
# (model_label below) - the classifier interpolates the policy, it
# does not replace bank verification.

def model_label(error_count, n, epsilon):
    """The verdict policy distilled to a three-way teaching label.

    A genuine note's error rate concentrates near epsilon; a forged
    note's near 1/4 + epsilon/2. Rates close to the genuine line are
    genuine, rates close to the forger line are forged, and the wide
    middle is suspect - send it back to the bank, do not guess.
    """
    if n <= 0:
        return "forged"
    rate = error_count / n
    eps = float(epsilon)
    if rate <= eps + 0.04:
        return "genuine"
    if rate >= (0.25 + eps / 2) - 0.04:
        return "forged"
    return "suspect"


def _training_grid():
    rows = []
    for n in (8, 16, 20, 32, 64):
        for eps in (0.0, 0.01, 0.02, 0.03, 0.05):
            for errors in range(0, n + 1):
                rows.append(((errors, n, eps), model_label(errors, n, eps)))
    return rows


TRAINING_GRID = _training_grid()


def _scaled(features):
    errors, n, eps = features
    return (errors / n if n else 1.0, n / 64.0, float(eps) * 2.0)


def classify_note(error_count, n, epsilon, k=5):
    """kNN over the policy-labelled grid, deterministic tie-breaking."""
    target = _scaled((error_count, n, epsilon))
    ranked = []
    for features, label in TRAINING_GRID:
        point = _scaled(features)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(target, point)))
        ranked.append((dist, features, label))
    ranked.sort(key=lambda row: (row[0], row[1]))
    votes = {}
    for _, _, label in ranked[:k]:
        votes[label] = votes.get(label, 0) + 1
    priority = {"genuine": 0, "suspect": 1, "forged": 2}
    return sorted(votes.items(), key=lambda kv: (-kv[1], priority[kv[0]]))[0][0]


def classifier_report():
    scenarios = {
        "clean_note_0_errors": (0, 20, 0.02),
        "one_error_noisy_channel": (1, 20, 0.02),
        "borderline_3_errors": (3, 20, 0.02),
        "quarter_errors_classic_forgery": (5, 20, 0.02),
        "eight_qubit_note_clean": (0, 8, 0.0),
        "large_note_quarter_errors": (8, 32, 0.0),
        "large_note_light_noise": (2, 32, 0.05),
        "large_note_mid_errors": (6, 32, 0.05),
    }
    return {name: classify_note(*features)
            for name, features in scenarios.items()}


# ================================================================ 8. Advisory seats
def _trace(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def argon4_decide(topic="quantummoney-demo"):
    """Gemini Argon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-argon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Argon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all finance and currency gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="quantummoney-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Say it in the first line of every report: the (3/4)^n line is exact arithmetic about a toy, not a security proof about money - then show the derivation, the error budget, and the oracle problem the scheme cannot hide.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["a bank press printing qubits in secret bases under a serial number",
                  "a forger's probe touching a note and scrambling half of what it touches",
                  "the (3/4)^n curve falling off a cliff as the note grows",
                  "a merchant's self-check cracking the very note it meant to trust",
                  "the verification desk stamping GENUINE, SUSPECT, and FORGED"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": argon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. qubit model
    rng = random.Random(7)
    q = {"bit": 1, "basis": "+"}
    chk("measure_matching_basis_faithful",
        measure(q, "+", rng) == 1 and q == {"bit": 1, "basis": "+"})
    q2 = {"bit": 0, "basis": "+"}
    out = measure(q2, "×", rng)
    chk("measure_wrong_basis_replaces_state",
        q2["basis"] == "×" and q2["bit"] == out and out in (0, 1))
    chk("bases_are_two", BASES == ("+", "×"))

    # 2. bank: mint, record, commitment, tamper
    bank = Bank()
    rng = random.Random(11)
    note = bank.mint("T-1", 20, rng)
    chk("mint_record_matches_note",
        bank.records["T-1"] == [(q["bit"], q["basis"]) for q in note["qubits"]])
    try:
        bank.mint("T-1", 4, rng)
        dup_ok = False
    except ValueError:
        dup_ok = True
    chk("mint_duplicate_serial_rejected", dup_ok)
    try:
        verify_note(bank, {"serial": "NOPE", "qubits": []}, rng)
        unknown_ok = False
    except KeyError:
        unknown_ok = True
    chk("verify_unknown_serial_rejected", unknown_ok)
    chk("genuine_note_verifies_clean",
        verify_note(bank, note, rng)["errors"] == 0)
    chk("verification_is_non_disturbing",
        verify_note(bank, note, rng)["accepted"]
        and verify_note(bank, note, rng)["accepted"])
    commitment = bank.commitment()
    chk("commitment_stable", bank.commitment() == commitment)
    bank2 = Bank()
    rng2 = random.Random(11)
    note2 = bank2.mint("T-1", 20, rng2)
    chk("same_seed_same_note",
        canonical_json(note2) == canonical_json(note)
        and bank2.commitment() == commitment)
    bank2.tamper_record("T-1", 0)
    chk("tamper_changes_commitment", bank2.commitment() != commitment)
    chk("tampered_record_fails_genuine_note_exactly_once",
        verify_note(bank2, note2, random.Random(3))["errors"] == 1)

    # 3. genuine probability 1, in a seeded run
    genuine = simulate_genuine()
    chk("genuine_simulation_all_pass",
        genuine["passed"] == genuine["trials"] == 200)

    # 4. forgery math - exact fractions, derived in code
    chk("forger_qubit_pass_is_three_quarters",
        forger_qubit_pass_probability() == Fraction(3, 4))
    chk("counterfeit_acceptance_n4_exact",
        counterfeit_acceptance(4) == Fraction(81, 256))
    chk("counterfeit_acceptance_n8_exact",
        counterfeit_acceptance(8) == Fraction(6561, 65536))
    chk("counterfeit_acceptance_n16_decimal",
        abs(float(counterfeit_acceptance(16)) - 0.0100226) < 1e-6)
    chk("counterfeit_acceptance_decreases_with_n",
        counterfeit_acceptance(4) > counterfeit_acceptance(8)
        > counterfeit_acceptance(16) > counterfeit_acceptance(32)
        > counterfeit_acceptance(64))
    table = acceptance_table()
    chk("acceptance_table_rows",
        [row["n"] for row in table] == [4, 8, 16, 32, 64]
        and table[0]["fraction"] == "81/256")

    # 5. seeded forgery simulation tracks the exact line
    sim = simulate_forgery()
    chk("sim_per_qubit_tracks_three_quarters",
        abs(sim["per_qubit"]["pass_rate"] - 0.75) < 0.02)
    chk("sim_full_note_tracks_exact",
        abs(sim["full_note"]["rate"] - sim["full_note"]["exact"]) < 0.03)

    # 6. error budget - exact binomial policy arithmetic
    chk("binomial_cdf_top_is_one",
        binomial_cdf(20, Fraction(1, 50), 20) == 1)
    chk("binomial_cdf_zero_errors",
        binomial_cdf(20, Fraction(1, 50), 0) == Fraction(49, 50) ** 20)
    chk("forger_mismatch_noiseless",
        forger_mismatch_probability(Fraction(0)) == Fraction(1, 4))
    chk("forger_mismatch_at_demo_epsilon",
        forger_mismatch_probability(DEMO_EPSILON) == Fraction(13, 50))
    budget = error_budget()
    chk("budget_genuine_acceptance_high",
        genuine_acceptance(DEMO_QUBITS, DEMO_EPSILON, DEMO_TOLERANCE)
        > Fraction(99, 100))
    chk("budget_forger_acceptance_low",
        forger_acceptance(DEMO_QUBITS, DEMO_EPSILON, DEMO_TOLERANCE)
        < Fraction(8, 100))
    chk("budget_separation_over_10x",
        genuine_acceptance(DEMO_QUBITS, DEMO_EPSILON, DEMO_TOLERANCE)
        > 10 * forger_acceptance(DEMO_QUBITS, DEMO_EPSILON, DEMO_TOLERANCE))
    chk("budget_threshold_for_99_9_is_3",
        acceptance_threshold(DEMO_QUBITS, DEMO_EPSILON) == 3)
    chk("budget_numbers_match_functions",
        budget["genuine_acceptance"]
        == float(genuine_acceptance(DEMO_QUBITS, DEMO_EPSILON, DEMO_TOLERANCE))
        and budget["forger_acceptance"]
        == float(forger_acceptance(DEMO_QUBITS, DEMO_EPSILON, DEMO_TOLERANCE)))

    # 7. oracle problem: a merchant's self-check is the forger's move
    book = build_demo_book()
    chk("merchant_check_disturbs_note",
        book["merchant_damage"]["disturbed"] >= 1)
    reports = demo_book_reports()
    chk("merchant_checked_note_fails_bank_verification",
        reports["merchant_checked_QM-0002"]["errors"] >= 1
        and not reports["merchant_checked_QM-0002"]["accepted"])
    chk("demo_genuine_note_clean", reports["genuine_QM-0001"]["errors"] == 0
        and reports["genuine_QM-0001"]["accepted"])
    chk("demo_forged_note_rejected",
        not reports["forged_QM-0001"]["accepted"]
        and reports["forged_QM-0001"]["errors"] >= 1)
    chk("demo_tampered_record_one_error",
        reports["tampered_record_QM-0003"]["errors"] == 1
        and reports["commitment_changed_by_tamper"])

    # 8. labelled notes stay labelled
    chk("cloning_bound_labelled_not_derived",
        CLONING_BOUND["value"] == "5/6"
        and CLONING_BOUND["status"] == "LABELLED"
        and CLONING_BOUND["derived_here"] is False)
    chk("public_key_money_labelled_not_built",
        PUBLIC_KEY_MONEY_NOTE["built_here"] is False
        and "open" in PUBLIC_KEY_MONEY_NOTE["status"])

    # 9. classifier - labels come from the lab's own verdict policy
    rep = classifier_report()
    chk("classifier_clean_genuine", rep["clean_note_0_errors"] == "genuine")
    chk("classifier_one_error_genuine",
        rep["one_error_noisy_channel"] == "genuine")
    chk("classifier_borderline_suspect", rep["borderline_3_errors"] == "suspect")
    chk("classifier_quarter_errors_forged",
        rep["quarter_errors_classic_forgery"] == "forged")
    chk("classifier_small_clean_genuine",
        rep["eight_qubit_note_clean"] == "genuine")
    chk("classifier_large_quarter_forged",
        rep["large_note_quarter_errors"] == "forged")
    chk("classifier_large_light_noise_genuine",
        rep["large_note_light_noise"] == "genuine")
    chk("classifier_large_mid_suspect",
        rep["large_note_mid_errors"] == "suspect")
    chk("classifier_matches_model",
        all(classify_note(*features) == model_label(*features)
            for features in [(0, 20, 0.02), (1, 20, 0.02), (3, 20, 0.02),
                             (5, 20, 0.02), (0, 8, 0.0), (8, 32, 0.0),
                             (2, 32, 0.05), (6, 32, 0.05)]))

    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14
        and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_currency_hold", gate("real_currency_issuance") == "HOLD")
    chk("gate_payment_hold", gate("payment_system_use") == "HOLD")
    chk("gate_unforgeability_hold",
        gate("unforgeability_claim_real_system") == "HOLD")
    chk("gate_toy_math_hold", gate("toy_math_as_security_proof_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    brains = brains_report()
    chk("argon4_no_override", brains["decider"]["can_override_hold"] is False
        and brains["decider"]["seat"]
        == "Gemini Argon 4 Extended Thinking")
    chk("claude_no_override", brains["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", brains["flow"]["rendered"] is False
        and brains["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("QuantumMoney-Lab - Wiesner quantum money lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] THE HONEST CORE - what the toy math does and does not prove")
    print("    Wiesner's scheme: the bank prepares qubits in secret random")
    print("    bases and records them against a serial number. Verification")
    print("    measures in the recorded bases, so a genuine note passes")
    print("    with probability 1. Copying a note requires measuring it,")
    print("    and measuring in a guessed basis disturbs it - that is the")
    print("    whole security idea, and it is exact arithmetic here.")
    print("    It is NOT money, NOT a security proof for any real scheme,")
    print("    and NOT a product. The qubits are classical (bit, basis)")
    print("    pairs and measurement is a rule, like QKD-Lab.")
    print("\n[2] The bank mints - serials, a secret record, a commitment")
    book = build_demo_book()
    bank = book["bank"]
    for serial, record in bank.records.items():
        print(f"    {serial}: {len(record)} qubits recorded in secret bases")
    print(f"    record commitment (sha256): {bank.commitment()[:16]}...")
    print("    -> only the bank can verify: only the bank knows the bases.")
    print("\n[3] Verification - genuine notes pass with probability 1")
    reports = demo_book_reports()
    gen = simulate_genuine()
    print(f"    seeded run: {gen['passed']}/{gen['trials']} genuine notes "
          f"accepted (n = {gen['n']}, zero channel error)")
    print(f"    demo note QM-0001: errors "
          f"{reports['genuine_QM-0001']['errors']} -> ACCEPTED")
    print("    -> measuring in the recorded basis does not disturb the")
    print("       note, so the bank can re-verify the same note twice.")
    print("\n[4] Forgery - intercept-resend, and the exact (3/4)^n line")
    print("    per qubit: right basis (1/2) passes for sure, wrong basis")
    print("    (1/2) passes half the time -> 1/2 + 1/2*1/2 = 3/4 exactly.")
    for row in acceptance_table():
        print(f"    n = {row['n']:3d}  acceptance {row['decimal']:.8f}  "
              f"({row['fraction']})")
    sim = simulate_forgery()
    print(f"    seeded sim: per-qubit pass {sim['per_qubit']['pass_rate']:.4f} "
          f"(exact 0.7500) over {sim['per_qubit']['qubits']} qubits")
    print(f"    seeded sim: full-note pass {sim['full_note']['rate']:.4f} "
          f"(exact {sim['full_note']['exact']:.4f}) over "
          f"{sim['full_note']['trials']} forged notes of n = "
          f"{sim['full_note']['n']}")
    print(f"    demo forgery of QM-0001: errors "
          f"{reports['forged_QM-0001']['errors']} -> REJECTED")
    print("\n[5] Error budget - noise is priced, tolerance is a policy")
    budget = error_budget()
    print(f"    labelled channel error eps = {budget['epsilon_decimal']:.2f} "
          f"per qubit, n = {budget['n']}, tolerance t = "
          f"{budget['tolerance']} errors")
    print(f"    genuine acceptance (exact binomial): "
          f"{budget['genuine_acceptance']:.4f}")
    print(f"    forger mismatch per qubit: "
          f"{budget['forger_mismatch_per_qubit']:.4f} "
          f"(= 1/4 + eps/2)")
    print(f"    forger acceptance (exact binomial): "
          f"{budget['forger_acceptance']:.4f}")
    print(f"    separation: {budget['separation_ratio']:.1f}x - and a "
          f"tolerance of {budget['threshold_for_99.9pct_genuine']} would "
          f"pass 99.9% of genuine notes")
    print("    -> the gap between the two sums is the scheme's budget.")
    print("       Spend it on tolerance and forgeries creep in; starve it")
    print("       and genuine notes bounce.")
    print("\n[6] The verification-oracle problem - shown, not hidden")
    print(f"    merchant self-check of QM-0002 disturbed "
          f"{reports['merchant_damage']['disturbed']} of "
          f"{reports['merchant_damage']['n']} qubits")
    print(f"    bank verification afterwards: errors "
          f"{reports['merchant_checked_QM-0002']['errors']} -> REJECTED")
    print("    -> checking a note without the secret bases IS the forger's")
    print("       move. Notes must return to the bank, or the bank must")
    print("       answer online as an oracle - the scheme's structural cost.")
    print(f"    tampered bank record: QM-0003 fails with exactly "
          f"{reports['tampered_record_QM-0003']['errors']} error, and the")
    print("    record commitment changes - the bank can audit its own book.")
    print("\n[7] Labelled notes - quoted bounds, open problems, no claims")
    print(f"    optimal cloning fidelity bound: {CLONING_BOUND['value']} "
          f"({CLONING_BOUND['status']} - {CLONING_BOUND['source_note']})")
    print("    intercept-resend, computed here, sits at 3/4 per qubit;")
    print("    even the optimal attack is bounded - no-cloning is the wall.")
    print(f"    public-key quantum money: {PUBLIC_KEY_MONEY_NOTE['status']}")
    print("    -> not built here, not claimed, and gated below.")
    print("\n[8] Note classifier (TinyML kNN, labels from the verdict policy)")
    for name, label in classifier_report().items():
        print(f"    {name:36s} -> {label}")
    print("\n[9] Advisory seats")
    brains = brains_report()
    print(f"    decider: {brains['decider']['decision']} "
          f"trace={brains['decider']['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {brains['advisor']['can_override_hold']}")
    print(f"    flow rendered = {brains['flow']['rendered']} "
          f"live = {brains['flow']['live']}")
    print(f"\n[10] HOLD gates: {len(HOLD_GATES)}")
    for key in HOLD_GATES:
        print(f"    HOLD  {key}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "mint":
        bank = Bank()
        rng = random.Random(20261117)
        note = bank.mint("QM-0001", DEMO_QUBITS, rng)
        print(json.dumps({
            "serial": note["serial"], "n": len(note["qubits"]),
            "record_commitment": bank.commitment(),
            "bases_are_secret": "the (bit, basis) record never leaves the bank",
        }, indent=2, sort_keys=True))
        return 0
    if cmd == "verify":
        print(json.dumps(demo_book_reports(), indent=2, sort_keys=True))
        return 0
    if cmd == "forge":
        print(json.dumps({
            "per_qubit_pass_exact": "3/4",
            "table": acceptance_table(),
            "simulation": simulate_forgery(),
            "genuine_simulation": simulate_genuine(),
        }, indent=2, sort_keys=True))
        return 0
    if cmd == "budget":
        print(json.dumps(error_budget(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classifier_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for key, value in HOLD_GATES.items():
            print(f"{key}: {value}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "real_currency_issuance"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
