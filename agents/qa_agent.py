"""
QA Agent — finds the gaps everyone else missed.

Given what product wants and what engineering estimates, this agent identifies
what needs to be tested, what edge cases are going to bite us in production,
and which stories are missing acceptance criteria that QA can actually verify.
"""


class QAAgent:
    def run(self, product_output: dict, engineer_output: dict, sprint_context: dict) -> dict:
        pass
