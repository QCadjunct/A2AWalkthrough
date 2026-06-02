"""The governed Policy agent — Lab 2's answerer.

PDF via data_path (shared repo-root data/), model via Settings.litellm_model,
config via Settings. Exposes answer_query(prompt) -> str for the executor.
"""

from __future__ import annotations

import base64
import os

import litellm

from a2a_labs.config import get_settings
from a2a_labs.paths import data_path
from a2a_labs.vendors import VendorModel

POLICY_PDF = "2026AnthemgHIPSBC.pdf"
POLICY_MODEL = VendorModel.GEMINI_FLASH_LITE

_SYSTEM_PROMPT = (
    "You are an expert insurance agent designed to assist with coverage "
    "queries. Use the provided documents to answer questions about insurance "
    "policies. If the information is not available in the documents, respond "
    "with 'I don't know'"
)


class PolicyAgent:
    """Answers insurance-coverage questions from the governed policy PDF."""

    def __init__(self) -> None:
        self._settings = get_settings()
        if self._settings.gemini_api_key and not os.environ.get("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = self._settings.gemini_api_key
        pdf = data_path(POLICY_PDF)
        with pdf.open("rb") as file:
            self._pdf_data = base64.standard_b64encode(file.read()).decode("utf-8")

    def answer_query(self, prompt: str) -> str:
        """Answer one coverage question, grounded in the policy PDF."""
        response = litellm.completion(
            model=self._settings.litellm_model(POLICY_MODEL),
            reasoning_effort="minimal",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{self._pdf_data}"
                            },
                        },
                    ],
                },
            ],
        )
        return response.choices[0].message.content.replace("$", r"\$")
