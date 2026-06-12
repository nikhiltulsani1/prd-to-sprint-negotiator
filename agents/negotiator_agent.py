"""
Negotiator Agent — where the arguing actually happens.

Takes the three agent outputs and finds a realistic middle ground. Applies
sprint capacity constraints, resolves priority conflicts between product and
engineering, and decides what gets cut versus what gets phased into a later sprint.
"""


class NegotiatorAgent:
    def run(self, product_output: dict, engineer_output: dict, qa_output: dict, sprint_context: dict) -> dict:
        pass
