"""
Engineer Agent — the one who asks "have you considered how hard this actually is?"

Takes the product output and puts story point estimates on everything. Also
flags the technical risks that product managers tend to wave away — things like
third-party dependencies, data migrations, and anything that touches auth.
"""

from agents.foundry_client import FoundryClient

SYSTEM_PROMPT = """You are a senior software engineer with 10 years experience.
You are reviewing a product feature list to estimate effort and flag risks.
Be realistic and specific — not every feature is a 3, not everything is high risk.
Return ONLY valid JSON with exactly these keys:
- estimates: list of objects, each with:
  - feature_id: string (matches F1, F2 etc from input)
  - feature_name: string
  - story_points: number (use fibonacci: 1,2,3,5,8,13)
  - complexity: string (Low/Medium/High)
  - technical_risks: list of strings (specific risks, not generic)
  - missing_requirements: list of strings (what's unclear or missing)
  - subtasks: list of strings (main implementation tasks)
- total_points: number (sum of all story_points)
- sprint_capacity: number (default 40 points per sprint)
- recommended_sprint_size: number (how many features fit in one sprint)
- capacity_warning: string or null (warning if total exceeds capacity)"""

FIBONACCI = {1, 2, 3, 5, 8, 13}


class EngineerAgent:
    def __init__(self):
        self.client = FoundryClient()

    def run(self, product_output: dict, sprint_context: dict) -> dict:
        velocity = sprint_context.get("velocity", 1.0)
        effective_capacity = int(40 * velocity)

        features = product_output["features"]
        tech_stack = product_output.get("tech_stack", [])

        feature_summary = "\n".join(
            f"- {f['id']}: {f['name']} — {f['description']}\n"
            f"  User stories: {'; '.join(f['user_stories'])}\n"
            f"  Acceptance criteria: {'; '.join(f['acceptance_criteria'])}"
            for f in features
        )
        tech_summary = ", ".join(tech_stack) if tech_stack else "not specified"

        user_prompt = (
            f"Tech stack: {tech_summary}\n\n"
            f"Features to estimate:\n{feature_summary}\n\n"
            f"Sprint capacity: {effective_capacity} points "
            f"(40 base × {velocity} velocity factor)."
        )

        result = self.client.json_chat(SYSTEM_PROMPT, user_prompt)

        if "estimates" not in result:
            raise ValueError("Engineer agent response missing 'estimates' key")

        # clamp any non-fibonacci points to nearest fibonacci value
        for est in result["estimates"]:
            pts = est.get("story_points", 3)
            if pts not in FIBONACCI:
                est["story_points"] = min(FIBONACCI, key=lambda f: abs(f - pts))

        # recalculate total from our (possibly clamped) estimates
        result["total_points"] = sum(e["story_points"] for e in result["estimates"])
        result["sprint_capacity"] = effective_capacity

        # override capacity_warning based on our own calculation
        if result["total_points"] > effective_capacity:
            over_by = result["total_points"] - effective_capacity
            result["capacity_warning"] = (
                f"Total {result['total_points']} pts exceeds sprint capacity "
                f"of {effective_capacity} pts by {over_by} pts."
            )
        else:
            result["capacity_warning"] = None

        return result
