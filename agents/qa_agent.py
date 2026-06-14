"""
QA Agent — finds the gaps everyone else missed.

Given what product wants and what engineering estimates, this agent identifies
what needs to be tested, what edge cases are going to bite us in production,
and which stories are missing acceptance criteria that QA can actually verify.

Runs one LLM call per feature in parallel (max 3 at once) instead of batching
all features in a single prompt — keeps each call focused and cuts wall-clock
time from ~45s down to the time of the slowest single feature.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.foundry_client import FoundryClient
from agents.standards_loader import load_standards

SYSTEM_PROMPT = """You are a senior QA engineer with 10 years experience in software testing.
You are reviewing a single feature and its engineering estimate to identify quality risks.
Be specific — generic statements like 'test the login' are not useful.
Reference actual field names, HTTP methods, and edge cases.
Return ONLY valid JSON with exactly these keys:
- feature_id: string
- feature_name: string
- test_cases: list of strings (specific, actionable test cases)
- edge_cases: list of strings (boundary conditions, failure scenarios)
- missing_acceptance_criteria: list of strings (gaps in the AC)
- qa_effort_points: number (1-5, additional QA effort needed)
- risk_level: string (Low/Medium/High)
- flagged: boolean (true if this feature needs discussion before sprint)"""


class QAAgent:
    def __init__(self):
        self.client = FoundryClient()

    def _get_estimate(self, engineer_output: dict, feature_id: str) -> dict:
        for est in engineer_output["estimates"]:
            if est["feature_id"] == feature_id:
                return est
        return {}

    def _review_feature(self, feature: dict, engineer_estimate: dict) -> dict:
        """Review a single feature — called in parallel per feature."""
        eng = engineer_estimate
        user_prompt = (
            f"Feature {feature['id']}: {feature['name']} (priority: {feature['priority']})\n"
            f"Description: {feature['description']}\n"
            f"Acceptance criteria: {'; '.join(feature['acceptance_criteria'])}\n"
            f"Story points: {eng.get('story_points', '?')} | Complexity: {eng.get('complexity', '?')}\n"
            f"Engineering risks: {'; '.join(eng.get('technical_risks', []))}\n"
            f"Missing requirements (from eng): {'; '.join(eng.get('missing_requirements', []))}"
        )
        system_prompt = SYSTEM_PROMPT
        if self._standards_content:
            system_prompt += f"\n\nApply these team QA standards to your review:\n{self._standards_content}"
        return self.client.json_chat(system_prompt, user_prompt)

    def run(self, product_output: dict, engineer_output: dict, sprint_context: dict) -> dict:
        # resolve standards content (UI passes string directly; CLI loads from file)
        standards_content = sprint_context.get("standards", "")
        if not standards_content:
            standards = load_standards()
            standards_content = standards.get("content", "")
        self._standards_content = standards_content

        features = product_output["features"]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self._review_feature,
                    f,
                    self._get_estimate(engineer_output, f["id"]),
                ): f
                for f in features
            }
            results = []
            for future in as_completed(futures):
                results.append(future.result())

        # restore feature order (as_completed returns in completion order)
        results.sort(key=lambda x: x["feature_id"])

        flagged_features = [r["feature_name"] for r in results if r.get("flagged", False)]
        total_qa_effort = sum(r.get("qa_effort_points", 0) for r in results)

        # overall risk = highest individual risk level
        risk_rank = {"Low": 0, "Medium": 1, "High": 2}
        overall = max(results, key=lambda r: risk_rank.get(r.get("risk_level", "Low"), 0))
        overall_quality_risk = overall.get("risk_level", "Medium")

        return {
            "qa_review": results,
            "total_qa_effort": total_qa_effort,
            "flagged_features": flagged_features,
            "overall_quality_risk": overall_quality_risk,
        }
