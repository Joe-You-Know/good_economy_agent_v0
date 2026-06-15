import json
import urllib.error
import urllib.request
from typing import Any, Dict

from .models import Opportunity


class OpenAIPlanner:
    """Optional model-assisted drafting.

    This adapter is intentionally small and side-effect free except for one API
    request. It does not browse, publish, contact anyone, or collect revenue.
    """

    endpoint = "https://api.openai.com/v1/responses"

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 45):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = int(timeout_seconds)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def draft_public_artifact_notes(self, opportunity: Opportunity, methodology: str, max_output_tokens: int) -> Dict[str, Any]:
        if not self.available:
            return {
                "ok": False,
                "error": "OPENAI_API_KEY is not configured.",
                "text": "",
            }

        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "You help draft public-good artifacts for a zero-negative-ethics "
                        "economic agent. Be truthful, practical, non-deceptive, and explicit "
                        "about limits. Do not suggest cold outreach, fake engagement, legal "
                        "claims, medical claims, financial advice, scraping, spam, or hidden fees."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Methodology summary:\n"
                        f"{methodology[:4000]}\n\n"
                        "Opportunity:\n"
                        f"{json.dumps(opportunity.to_dict(), indent=2, sort_keys=True)}\n\n"
                        "Draft a concise supplemental section with practical implementation "
                        "ideas, verification steps, and limitations. Return plain markdown only."
                    ),
                },
            ],
            "max_output_tokens": int(max_output_tokens),
        }

        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return {
                "ok": False,
                "error": f"OpenAI HTTP error {exc.code}: {_safe_error_body(exc)}",
                "text": "",
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {
                "ok": False,
                "error": f"OpenAI request failed: {exc}",
                "text": "",
            }

        text = _extract_response_text(response_data)
        return {
            "ok": bool(text),
            "error": "" if text else "OpenAI response did not contain text.",
            "text": text,
            "model": self.model,
        }


def _extract_response_text(response_data: Dict[str, Any]) -> str:
    direct = response_data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    parts = []
    for output_item in response_data.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n\n".join(parts).strip()


def _safe_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return "no response body"
    if len(body) > 500:
        return body[:500] + "..."
    return body
