"""
Output Agent — turns the negotiated mess into something a team can actually use.

Takes the agreed-upon backlog and formats it as clean markdown: stories with
estimates, acceptance criteria, test requirements, and anything flagged for
the next sprint. The goal is something you can paste straight into Jira or Linear.
"""


class OutputAgent:
    def run(self, negotiated: dict, sprint_context: dict) -> str:
        pass
