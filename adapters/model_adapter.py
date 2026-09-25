"""
Model adapter — Gemini, matching the actor named in the case's own
Components Map template (and this workspace already has Gemini plumbing in
sibling projects: Pre-Read Companion, movie-match).

The exact model name is [PENDING] per the task's API-details list, so it's
env-configurable rather than hardcoded, and this adapter fails closed into
a clearly-labeled mock rather than silently pretending to have called a
model. Nothing here claims a successful integration that hasn't actually
been run against a real key.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ModelResponse:
    text: str
    mocked: bool


class ModelAdapter:
    """
    Thin wrapper so pipeline.py and the node runners never import
    google.generativeai directly. Swapping providers later means editing
    this one file.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # gemini-2.0-flash was retired by Google during development of this
        # adapter (confirmed by a live 404 pointing here); gemini-3.6-flash
        # is the replacement Google's own error message names, and matches
        # the placeholder already present in this workspace's root
        # .env.example. Still treat this as unconfirmed/overridable, not a
        # hardcoded guarantee — override via GEMINI_MODEL if it changes again.
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self._client = None

        if self.api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model_name)
            except Exception as exc:  # pragma: no cover - defensive only
                # Fail closed into mock mode rather than crashing the
                # pipeline; the caller sees mocked=True and can decide what
                # to do (this project's CLI surfaces it loudly).
                self._client = None
                self._init_error = str(exc)

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def generate(self, system_context: str, prompt: str) -> ModelResponse:
        if not self._client:
            return ModelResponse(
                text=(
                    "[MOCK MODE — no live GEMINI_API_KEY/model configured. "
                    "This is a placeholder, not a real triage/draft result. "
                    "Set GEMINI_API_KEY and GEMINI_MODEL in .env to get real "
                    "output.]"
                ),
                mocked=True,
            )

        full_prompt = f"{system_context}\n\n---\n\n{prompt}"
        try:
            response = self._client.generate_content(full_prompt)
            return ModelResponse(text=response.text, mocked=False)
        except Exception as exc:
            # A live-call failure (bad model name, quota, network) must not
            # crash the pipeline or be silently swallowed as a real result.
            # Surface it as an explicit, labeled error so the review file
            # shows a failed call, not a fabricated verdict/draft.
            return ModelResponse(
                text=(
                    f"[MODEL CALL FAILED — {type(exc).__name__}: {exc}. "
                    "No real triage/draft was produced for this note.]"
                ),
                mocked=True,
            )
