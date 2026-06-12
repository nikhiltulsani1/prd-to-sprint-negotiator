"""Basic smoke tests — checks the agents exist and return without blowing up."""

import os
import pytest

# resolve sample path relative to this file so tests run from any directory
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")
SAMPLE_PRD = os.path.join(SAMPLES_DIR, "sample_prd.txt")


# ---------------------------------------------------------------------------
# Existence checks (no API calls)
# ---------------------------------------------------------------------------

def test_product_agent_exists():
    from agents.product_agent import ProductAgent
    assert hasattr(ProductAgent(), "run")

def test_engineer_agent_exists():
    from agents.engineer_agent import EngineerAgent
    assert hasattr(EngineerAgent(), "run")

def test_qa_agent_exists():
    from agents.qa_agent import QAAgent
    assert hasattr(QAAgent(), "run")

def test_negotiator_agent_exists():
    from agents.negotiator_agent import NegotiatorAgent
    assert hasattr(NegotiatorAgent(), "run")

def test_output_agent_exists():
    from agents.output_agent import OutputAgent
    assert hasattr(OutputAgent(), "run")


# ---------------------------------------------------------------------------
# ProductAgent — sprint 1 (full PRD)
# ---------------------------------------------------------------------------

def test_product_agent_sprint1():
    from agents.product_agent import ProductAgent

    with open(SAMPLE_PRD) as f:
        prd = f.read()

    result = ProductAgent().run(prd, {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0})

    assert "features" in result
    assert len(result["features"]) > 0

    print(f"\nProject: {result['project_name']}")
    print(f"Total features: {result['total_features']}")
    print("\nFeatures extracted:")
    for feature in result["features"]:
        assert "id" in feature
        assert "name" in feature
        assert "priority" in feature
        assert "user_stories" in feature
        print(f"  {feature['id']} | {feature['name']:<30} | {feature['priority']}")


# ---------------------------------------------------------------------------
# ProductAgent — sprint 2 (User Authentication already done)
# ---------------------------------------------------------------------------

def test_product_agent_sprint2_filters_completed():
    from agents.product_agent import ProductAgent

    with open(SAMPLE_PRD) as f:
        prd = f.read()

    result = ProductAgent().run(prd, {
        "sprint": 2,
        "completed": ["User Authentication"],
        "blocked": [],
        "velocity": 0.9,
    })

    feature_names = [f["name"] for f in result["features"]]

    assert not any("authentication" in name.lower() for name in feature_names), (
        f"'User Authentication' should have been filtered out but got: {feature_names}"
    )

    print(f"\nSprint 2 — features remaining after filtering completed:")
    for name in feature_names:
        print(f"  - {name}")


# ---------------------------------------------------------------------------
# EngineerAgent — sprint 1 (full estimates)
# ---------------------------------------------------------------------------

def _get_product_output(sprint_context=None):
    """Helper — runs ProductAgent so EngineerAgent tests have real input."""
    from agents.product_agent import ProductAgent
    ctx = sprint_context or {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0}
    with open(SAMPLE_PRD) as f:
        prd = f.read()
    return ProductAgent().run(prd, ctx)


FIBONACCI = {1, 2, 3, 5, 8, 13}


def test_engineer_agent_sprint1():
    from agents.engineer_agent import EngineerAgent

    product_output = _get_product_output()
    result = EngineerAgent().run(product_output, {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0})

    assert "estimates" in result
    assert len(result["estimates"]) > 0

    recalculated_total = sum(e["story_points"] for e in result["estimates"])
    assert result["total_points"] == recalculated_total, (
        f"total_points {result['total_points']} doesn't match sum {recalculated_total}"
    )

    print(f"\nSprint capacity: {result['sprint_capacity']} pts")
    print(f"Total estimated: {result['total_points']} pts")
    print(f"Recommended sprint size: {result.get('recommended_sprint_size')} features")
    print(f"Capacity warning: {result['capacity_warning'] or 'none'}")
    print("\nEstimates:")
    for est in result["estimates"]:
        pts = est["story_points"]
        assert pts in FIBONACCI, f"{est['feature_id']} has non-fibonacci points: {pts}"
        assert 1 <= pts <= 13
        print(f"  {est['feature_id']} | {est['feature_name']:<30} | {pts:>2} pts | {est['complexity']}")
        if est["technical_risks"]:
            print(f"       Risks: {'; '.join(est['technical_risks'])}")


# ---------------------------------------------------------------------------
# EngineerAgent — velocity 0.8 triggers capacity warning
# ---------------------------------------------------------------------------

def test_engineer_agent_capacity_warning_at_low_velocity():
    from agents.engineer_agent import EngineerAgent

    product_output = _get_product_output()
    result = EngineerAgent().run(product_output, {"sprint": 1, "completed": [], "blocked": [], "velocity": 0.8})

    effective_capacity = int(40 * 0.8)  # 32 pts

    print(f"\nVelocity 0.8 — effective capacity: {effective_capacity} pts")
    print(f"Total estimated: {result['total_points']} pts")
    print(f"Capacity warning: {result['capacity_warning'] or 'none'}")

    if result["total_points"] > effective_capacity:
        assert result["capacity_warning"] is not None, (
            f"Expected a capacity warning — total {result['total_points']} > capacity {effective_capacity}"
        )
        print("Capacity warning correctly raised.")


# ---------------------------------------------------------------------------
# QAAgent
# ---------------------------------------------------------------------------

def _get_engineer_output(product_output=None):
    """Helper — runs EngineerAgent so QAAgent tests have real input."""
    from agents.engineer_agent import EngineerAgent
    if product_output is None:
        product_output = _get_product_output()
    return EngineerAgent().run(product_output, {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0})


def test_qa_agent_sprint1():
    from agents.qa_agent import QAAgent

    product_output = _get_product_output()
    engineer_output = _get_engineer_output(product_output)
    result = QAAgent().run(product_output, engineer_output, {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0})

    assert "qa_review" in result
    assert len(result["qa_review"]) > 0

    print(f"\nOverall quality risk: {result['overall_quality_risk']}")
    print(f"Total QA effort: {result['total_qa_effort']} pts")
    print(f"Flagged for discussion: {result['flagged_features'] or 'none'}")
    print("\nQA Review:")

    for item in result["qa_review"]:
        assert "test_cases" in item
        assert "edge_cases" in item
        assert len(item["test_cases"]) > 0
        assert len(item["edge_cases"]) > 0

        # each test case should be specific — not just "test login"
        for tc in item["test_cases"]:
            assert len(tc) > 20, f"Test case too vague ({len(tc)} chars): '{tc}'"

        flagged_marker = " [FLAGGED]" if item.get("flagged") else ""
        print(f"\n  {item['feature_id']} | {item['feature_name']}{flagged_marker}")
        print(f"    Risk: {item['risk_level']} | QA effort: {item['qa_effort_points']} pts")
        print(f"    Test cases ({len(item['test_cases'])}):")
        for tc in item["test_cases"][:3]:  # show first 3 to keep output readable
            print(f"      - {tc}")
        if item["edge_cases"]:
            print(f"    Edge cases ({len(item['edge_cases'])}):")
            for ec in item["edge_cases"][:2]:
                print(f"      - {ec}")
        if item["missing_acceptance_criteria"]:
            print(f"    Missing AC: {'; '.join(item['missing_acceptance_criteria'][:2])}")


# ---------------------------------------------------------------------------
# NegotiatorAgent
# ---------------------------------------------------------------------------

def _get_qa_output(product_output=None, engineer_output=None):
    """Helper — runs QAAgent so NegotiatorAgent tests have real input."""
    from agents.qa_agent import QAAgent
    if product_output is None:
        product_output = _get_product_output()
    if engineer_output is None:
        engineer_output = _get_engineer_output(product_output)
    return QAAgent().run(product_output, engineer_output, {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0})


def test_negotiator_agent_sprint1():
    from agents.negotiator_agent import NegotiatorAgent

    ctx = {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0}
    product_output  = _get_product_output(ctx)
    engineer_output = _get_engineer_output(product_output)
    qa_output       = _get_qa_output(product_output, engineer_output)

    result = NegotiatorAgent().run(product_output, engineer_output, qa_output, ctx)

    assert result["sprint_goal"], "sprint_goal must be a non-empty string"
    assert len(result["included_features"]) > 0, "at least one feature must be included"
    assert result["total_committed_points"] <= 40, (
        f"Committed {result['total_committed_points']} pts exceeds capacity 40"
    )

    print(f"\nSprint goal: {result['sprint_goal']}")
    print(f"Capacity: {result['effective_capacity']} pts | Committed: {result['total_committed_points']} pts")

    print("\nIncluded features:")
    for f in result["included_features"]:
        print(f"  {f['feature_id']} | {f['feature_name']:<30} | {f['story_points']} pts")
        print(f"    Why: {f['reason_included']}")

    if result["excluded_features"]:
        print("\nExcluded features:")
        for f in result["excluded_features"]:
            print(f"  {f['feature_id']} | {f['feature_name']:<30} | -> {f['recommended_sprint']}")
            print(f"    Why: {f['reason_excluded']}")

    print("\nNegotiation notes:")
    for note in result["negotiation_notes"]:
        print(f"  - {note}")

    print(f"\nTop risks:")
    for risk in result["risks"]:
        print(f"  - {risk}")


def test_negotiator_agent_sprint2_velocity_08():
    from agents.negotiator_agent import NegotiatorAgent

    ctx_s1 = {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0}
    product_s1  = _get_product_output(ctx_s1)
    engineer_s1 = _get_engineer_output(product_s1)
    qa_s1       = _get_qa_output(product_s1, engineer_s1)
    result_s1   = NegotiatorAgent().run(product_s1, engineer_s1, qa_s1, ctx_s1)
    s1_features = {f["feature_id"] for f in result_s1["included_features"]}

    ctx_s2 = {"sprint": 2, "completed": ["User Authentication"], "blocked": [], "velocity": 0.8}
    product_s2  = _get_product_output(ctx_s2)
    engineer_s2 = _get_engineer_output(product_s2)
    qa_s2       = _get_qa_output(product_s2, engineer_s2)
    result_s2   = NegotiatorAgent().run(product_s2, engineer_s2, qa_s2, ctx_s2)

    included_names = [f["feature_name"] for f in result_s2["included_features"]]
    assert not any("authentication" in n.lower() for n in included_names), (
        f"User Authentication should be excluded in sprint 2 but found: {included_names}"
    )
    assert result_s2["total_committed_points"] <= 32, (
        f"Sprint 2 committed {result_s2['total_committed_points']} pts exceeds capacity 32"
    )

    s2_features = {f["feature_id"] for f in result_s2["included_features"]}

    print(f"\nSprint 1 goal: {result_s1['sprint_goal']}")
    print(f"Sprint 1 scope: {sorted(s1_features)} | {result_s1['total_committed_points']} pts")

    print(f"\nSprint 2 goal: {result_s2['sprint_goal']}")
    print(f"Sprint 2 scope: {sorted(s2_features)} | {result_s2['total_committed_points']} pts / 32 cap")

    dropped = s1_features - s2_features
    added   = s2_features - s1_features
    if dropped:
        print(f"Dropped from sprint 1: {sorted(dropped)}")
    if added:
        print(f"New in sprint 2: {sorted(added)}")


# ---------------------------------------------------------------------------
# OutputAgent
# ---------------------------------------------------------------------------

def test_output_agent_sprint1():
    from agents.negotiator_agent import NegotiatorAgent
    from agents.output_agent import OutputAgent

    ctx = {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0, "project_name": "TaskFlow"}
    product_output  = _get_product_output(ctx)
    engineer_output = _get_engineer_output(product_output)
    qa_output       = _get_qa_output(product_output, engineer_output)
    negotiated      = NegotiatorAgent().run(product_output, engineer_output, qa_output, ctx)

    result = OutputAgent().run(negotiated, ctx)

    assert isinstance(result, str)
    assert len(result) > 500, f"Output too short: {len(result)} chars"
    assert "## Sprint Goal" in result
    assert "## Committed Scope" in result
    assert "## QA Checklist" in result

    output_path = os.path.join(os.path.dirname(__file__), "sample_output_sprint1.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nOutput saved to tests/sample_output_sprint1.md ({len(result)} chars)")

    print("\n--- First 50 lines ---")
    for line in result.splitlines()[:50]:
        print(line)


# ---------------------------------------------------------------------------
# End-to-end pipeline smoke test
# ---------------------------------------------------------------------------

def test_full_pipeline_sprint1():
    """Full pipeline smoke test — all 5 agents in sequence."""
    from agents.product_agent import ProductAgent
    from agents.engineer_agent import EngineerAgent
    from agents.qa_agent import QAAgent
    from agents.negotiator_agent import NegotiatorAgent
    from agents.output_agent import OutputAgent

    prd = open(SAMPLE_PRD).read()
    sprint_context = {"sprint": 1, "completed": [], "blocked": [], "velocity": 1.0}

    product = ProductAgent().run(prd, sprint_context)
    assert product and product.get('features')

    engineer = EngineerAgent().run(product, sprint_context)
    assert engineer and engineer.get('estimates')

    qa = QAAgent().run(product, engineer, sprint_context)
    assert qa and qa.get('qa_review')

    negotiated = NegotiatorAgent().run(product, engineer, qa, sprint_context)
    assert negotiated and negotiated.get('included_features')
    assert negotiated['total_committed_points'] <= 40

    output = OutputAgent().run(negotiated, sprint_context)
    assert isinstance(output, str) and len(output) > 500
    assert "## Sprint Goal" in output
    assert "## Committed Scope" in output

    print(f"\nFull pipeline passed")
    print(f"Committed: {negotiated['total_committed_points']} pts")
    print(f"Features: {len(negotiated['included_features'])} included, {len(negotiated['excluded_features'])} excluded")
