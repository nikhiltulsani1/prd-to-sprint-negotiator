"""
MCP Payload Generator

Generates a JSON payload compatible with common MCP clients (Jira, ADO, Linear)
from the negotiated sprint plan, QA output, and available context.
"""
from typing import Dict, Any, List


class MCPPayloadGenerator:
    def generate(self, negotiated: dict, qa_output: dict, sprint_context: dict, project_key: str = "PROJ") -> dict:
        sprint = sprint_context.get("sprint", negotiated.get("sprint_number", 1))
        sprint_goal = negotiated.get("sprint_goal", "")

        # try to find product and engineer outputs if the caller attached them to sprint_context
        product_output = sprint_context.get("product_output", {})
        engineer_output = sprint_context.get("engineer_output", {})

        # build lookup maps
        product_map = {}
        for f in product_output.get("features", []):
            # product features use key 'id'
            product_map[f.get("id")] = f

        eng_map = {}
        for e in engineer_output.get("estimates", []):
            eng_map[e.get("feature_id")] = e

        qa_map = {}
        for q in (qa_output or {}).get("qa_review", []):
            qa_map[q.get("feature_id")] = q

        epic_summary = f"Sprint {sprint} — {sprint_goal}" if sprint_goal else f"Sprint {sprint}"

        stories: List[Dict[str, Any]] = []
        for f in negotiated.get("included_features", []):
            fid = f.get("feature_id")
            prod = product_map.get(fid, {})
            eng = eng_map.get(fid, {})
            qa = qa_map.get(fid, {})

            feature_name = prod.get("name") or f.get("feature_name")
            story_points = eng.get("story_points") or f.get("story_points") or 0
            priority = prod.get("priority") or f.get("priority") or "Medium"
            acceptance = prod.get("acceptance_criteria") or f.get("acceptance_criteria") or []

            # build subtasks from engineer estimates
            subtasks = []
            for st in eng.get("subtasks", []) if eng.get("subtasks") else []:
                subtasks.append({
                    "tool": "create_issue",
                    "params": {
                        "issuetype": "Sub-task",
                        "summary": st,
                        "parent": feature_name,
                    },
                })

            # build QA tasks from QA output test cases
            qa_tasks = []
            for tc in qa.get("test_cases", []) if qa.get("test_cases") else []:
                qa_tasks.append({
                    "tool": "create_issue",
                    "params": {
                        "issuetype": "Sub-task",
                        "summary": f"QA: {tc}",
                        "parent": feature_name,
                        "labels": ["qa", "testing"],
                    },
                })

            story = {
                "tool": "create_issue",
                "params": {
                    "issuetype": "Story",
                    "project": project_key,
                    "summary": feature_name,
                    "story_points": story_points,
                    "priority": priority,
                    "epic_link": epic_summary,
                    "acceptance_criteria": "\n".join(acceptance) if isinstance(acceptance, list) else str(acceptance),
                    "labels": [f"sprint-{sprint}", "prd-negotiator"],
                },
                "subtasks": subtasks,
                "qa_tasks": qa_tasks,
            }

            stories.append(story)

        # deferred features
        deferred = []
        for ex in negotiated.get("excluded_features", []):
            deferred.append({
                "tool": "create_issue",
                "params": {
                    "issuetype": "Story",
                    "project": project_key,
                    "summary": ex.get("feature_name"),
                    "labels": [f"deferred-to-{ex.get('recommended_sprint', 'later')}"],
                    "description": ex.get("reason_excluded", "No reason provided"),
                },
            })

        total_stories = len(stories)
        total_story_points = sum(s["params"].get("story_points", 0) for s in stories)
        total_subtasks = sum(len(s.get("subtasks", [])) for s in stories)
        total_qa_tasks = sum(len(s.get("qa_tasks", [])) for s in stories)
        deferred_stories = len(deferred)

        payload = {
            "schema_version": "1.0",
            "generated_by": "PRD-to-Sprint Negotiator",
            "sprint": sprint,
            "project_key": project_key,
            "compatible_servers": ["jira-mcp", "azure-devops-mcp", "linear-mcp"],
            "epic": {
                "tool": "create_issue",
                "params": {
                    "issuetype": "Epic",
                    "project": project_key,
                    "summary": epic_summary,
                    "description": sprint_goal,
                },
            },
            "stories": stories,
            "deferred": deferred,
            "summary": {
                "total_stories": total_stories,
                "total_story_points": total_story_points,
                "total_subtasks": total_subtasks,
                "total_qa_tasks": total_qa_tasks,
                "deferred_stories": deferred_stories,
            },
        }

        return payload
