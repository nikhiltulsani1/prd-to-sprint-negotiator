"""
Negotiator Agent — where the arguing actually happens.

Takes the three agent outputs and finds a realistic middle ground. Applies
sprint capacity constraints, resolves priority conflicts between product and
engineering, and decides what gets cut versus what gets phased into a later sprint.
"""

from agents.foundry_client import FoundryClient

SYSTEM_PROMPT = """You are an experienced scrum master and technical lead.
You have inputs from three specialists — a product manager, an engineer, and a QA engineer.
Your job is to negotiate a realistic sprint plan that balances business value, technical feasibility, and quality.

Rules you must follow:
- Default sprint capacity is 40 story points
- Adjust capacity by velocity factor if provided (capacity * velocity)
- Target 70-80% of sprint capacity minimum (28-32 pts for a 40pt sprint)
- Only exclude a feature if it is QA-flagged AND has zero acceptance criteria
- Features with Medium QA risk can still be included with a note
- Never leave more than 30% capacity unused unless every remaining feature is blocked or has no acceptance criteria
- If you must under-commit, explain specifically why in negotiation_notes
- Always include at least one High priority feature
- If total points exceed capacity, cut lowest priority features first
- For sprint > 1, skip completed features entirely
- Blocked features from last sprint get re-estimated at original points
- Every exclusion must have a clear reason
- Every inclusion must fit within capacity

Return ONLY valid JSON with exactly these keys:
- sprint_goal: string (one sentence describing the sprint objective)
- sprint_number: number
- effective_capacity: number (40 * velocity)
- included_features: list of objects, each with:
  - feature_id: string
  - feature_name: string
  - story_points: number
  - reason_included: string
  - qa_requirements: list of strings (from QA agent)
- excluded_features: list of objects, each with:
  - feature_id: string
  - feature_name: string
  - reason_excluded: string
  - recommended_sprint: string (e.g. Sprint 2)
- carried_over: list of strings (blocked items from last sprint)
- total_committed_points: number
- negotiation_notes: list of strings (key decisions made and why)
- risks: list of strings (top 3 risks for this sprint)"""


class NegotiatorAgent:
    def __init__(self):
        self.client = FoundryClient()

    def run(self, product_output: dict, engineer_output: dict, qa_output: dict, sprint_context: dict) -> dict:
        sprint = sprint_context.get("sprint", 1)
        velocity = sprint_context.get("velocity", 1.0)
        completed = sprint_context.get("completed", [])
        blocked = sprint_context.get("blocked", [])
        effective_capacity = int(40 * velocity)

        # build lookup maps for quick cross-referencing
        engineer_map = {e["feature_id"]: e for e in engineer_output["estimates"]}
        qa_map = {q["feature_id"]: q for q in qa_output["qa_review"]}

        feature_lines = []
        for f in product_output["features"]:
            eng = engineer_map.get(f["id"], {})
            qa = qa_map.get(f["id"], {})
            line = (
                f"  {f['id']}: {f['name']} | Priority: {f['priority']} | "
                f"{eng.get('story_points', '?')} pts | Complexity: {eng.get('complexity', '?')} | "
                f"QA risk: {qa.get('risk_level', '?')} | QA flagged: {qa.get('flagged', False)}"
            )
            feature_lines.append(line)

        user_prompt = (
            f"Sprint {sprint} negotiation.\n"
            f"Effective capacity: {effective_capacity} pts (40 × {velocity} velocity).\n"
        )

        if completed:
            user_prompt += f"Already completed — skip entirely: {', '.join(completed)}.\n"
        if blocked:
            user_prompt += f"Blocked from last sprint — carry over: {', '.join(blocked)}.\n"

        user_prompt += f"\nFeatures (with cross-agent data):\n" + "\n".join(feature_lines)

        user_prompt += f"\n\nEngineering total: {engineer_output['total_points']} pts. "
        if engineer_output.get("capacity_warning"):
            user_prompt += f"WARNING: {engineer_output['capacity_warning']}"

        user_prompt += f"\nQA overall risk: {qa_output.get('overall_quality_risk', 'Unknown')}. "
        if qa_output.get("flagged_features"):
            user_prompt += f"Flagged features needing discussion: {', '.join(qa_output['flagged_features'])}."

        result = self.client.json_chat(SYSTEM_PROMPT, user_prompt)

        if "included_features" not in result or "excluded_features" not in result:
            raise ValueError("Negotiator response missing included_features or excluded_features")

        # safety net — trim lowest-point features if the model still went over capacity
        result["included_features"].sort(key=lambda f: f["story_points"])
        trimmed = []
        running_total = 0
        for feature in sorted(result["included_features"], key=lambda f: -f["story_points"]):
            if running_total + feature["story_points"] <= effective_capacity:
                trimmed.append(feature)
                running_total += feature["story_points"]
            else:
                result["excluded_features"].append({
                    "feature_id": feature["feature_id"],
                    "feature_name": feature["feature_name"],
                    "reason_excluded": f"Trimmed to fit sprint capacity of {effective_capacity} pts",
                    "recommended_sprint": f"Sprint {sprint + 1}",
                })

        result["included_features"] = trimmed
        result["total_committed_points"] = running_total
        result["effective_capacity"] = effective_capacity

        return result
