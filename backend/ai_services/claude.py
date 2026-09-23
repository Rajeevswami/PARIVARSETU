"""Anthropic Messages API with tool use. No Django view should import this module."""

import json
import urllib.request

from django.conf import settings


class ClaudeError(Exception):
    pass


class HttpClaudeTransport:
    def complete(self, *, system: str, messages: list, tools: list) -> dict:
        key = settings.ANTHROPIC_API_KEY
        if not key:
            raise ClaudeError("ANTHROPIC_API_KEY is not configured.")
        payload = {
            "model": settings.ANTHROPIC_MODEL,
            "max_tokens": 800,
            "system": system,
            "messages": messages,
            "tools": tools,
        }
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            method="POST",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
