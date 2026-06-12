"""
Engineer Agent — the one who asks "have you considered how hard this actually is?"

Takes the product output and puts story point estimates on everything. Also
flags the technical risks that product managers tend to wave away — things like
third-party dependencies, data migrations, and anything that touches auth.
"""


class EngineerAgent:
    def run(self, product_output: dict, sprint_context: dict) -> dict:
        pass
