"""
Product Agent — reads the PRD and pulls out what actually matters.

Extracts user stories, acceptance criteria, and feature groupings so the
rest of the agents have something concrete to work with rather than a wall
of marketing prose.
"""

from agents.foundry_client import FoundryClient

SYSTEM_PROMPT = """You are a senior product manager with 10 years experience.
Analyze the PRD and extract structured product information.
Return ONLY valid JSON with exactly these keys:
- project_name: string, the product name
- features: list of objects, each with:
  - id: string (F1, F2, F3...)
  - name: string
  - description: string
  - user_stories: list of strings (each starting with 'As a...')
  - acceptance_criteria: list of strings
  - priority: string (High/Medium/Low)
  - dependencies: list of feature ids this depends on (empty list if none)
- tech_stack: list of strings
- total_features: number"""

REQUIRED_KEYS = {"project_name", "features", "tech_stack", "total_features"}
REQUIRED_FEATURE_KEYS = {"id", "name", "description", "user_stories", "acceptance_criteria", "priority", "dependencies"}


class ProductAgent:
    def __init__(self):
        self.client = FoundryClient()

    def run(self, prd_content: str, sprint_context: dict) -> dict:
        sprint = sprint_context.get("sprint", 1)
        completed = sprint_context.get("completed", [])
        blocked = sprint_context.get("blocked", [])

        user_prompt = f"PRD:\n{prd_content}"

        if sprint > 1:
            user_prompt += f"\n\nSprint context: this is sprint {sprint}."
            if completed:
                user_prompt += f" The following features are already done — skip them in your output: {', '.join(completed)}."
            if blocked:
                user_prompt += f" These features are currently blocked — flag them: {', '.join(blocked)}."

        result = self.client.json_chat(SYSTEM_PROMPT, user_prompt)

        missing = REQUIRED_KEYS - result.keys()
        if missing:
            raise ValueError(f"Product agent response missing keys: {missing}")

        # filter out completed features when the team is past sprint 1
        if sprint > 1 and completed:
            completed_lower = [c.lower() for c in completed]
            result["features"] = [
                f for f in result["features"]
                if f["name"].lower() not in completed_lower
            ]
            result["total_features"] = len(result["features"])

        return result
