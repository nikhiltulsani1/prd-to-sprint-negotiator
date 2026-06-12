"""
Shared Azure AI Foundry client used by all agents.

Plain requests — no SDK — so we don't have to fight api-version negotiation.
"""

import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()


class FoundryClient:
    def __init__(self):
        self.endpoint = os.environ["AZURE_FOUNDRY_ENDPOINT"].rstrip("/")
        self.key = os.environ["AZURE_FOUNDRY_KEY"]
        self.deployment = os.getenv("AZURE_FOUNDRY_DEPLOYMENT", "gpt-4.1-mini")

        self._url = f"{self.endpoint}/chat/completions"
        self._headers = {
            "api-key": self.key,
            "Content-Type": "application/json",
        }

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat request and return the response text."""
        payload = {
            "model": self.deployment,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        for attempt in range(2):
            try:
                response = requests.post(
                    self._url,
                    headers=self._headers,
                    json=payload,
                    timeout=60,
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                last_error = e
                if attempt == 0:
                    continue  # retry once

        raise RuntimeError(
            f"Foundry request failed after 2 attempts: {last_error}"
        )

    def json_chat(self, system_prompt: str, user_prompt: str) -> dict | list:
        """Same as chat() but parses the response as JSON.

        Strips markdown code fences if the model wraps its output in them.
        Raises ValueError with the raw text if parsing fails.
        """
        raw = self.chat(system_prompt, user_prompt)

        # strip ```json ... ``` or ``` ... ``` wrappers
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(
                f"Response was not valid JSON.\n\nRaw response:\n{raw}"
            )


if __name__ == "__main__":
    client = FoundryClient()

    result = client.json_chat(
        system_prompt="Return ONLY a JSON array of 3 strings. No explanation, no markdown.",
        user_prompt="Give 3 sprint planning tips",
    )

    print(result)
    assert isinstance(result, list), f"Expected a list, got {type(result)}"
    print("OK: returned a list")
