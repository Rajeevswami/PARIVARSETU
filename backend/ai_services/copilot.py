"""Tool-use loop. Views call answer(); they do not select tools themselves."""

import json
import os

from apps.billing.services.entitlements import ai_allowed
from apps.common.exceptions import ApplicationError
from apps.common.features import is_enabled
from apps.families.models import Family

from .claude import HttpClaudeTransport
from .tools import TOOL_DEFINITIONS, run_tool

SYSTEM = (
    "You are the FamilyNexus ledger copilot. Answer in the user's language, Hindi or English. "
    "Use tools for numbers. Do not invent balances. You are not a bank, lawyer, or tax adviser."
)


def assistant_enabled(family) -> bool:
    forced = os.environ.get("FEATURE_AI_COPILOT")
    if forced is not None:
        return forced.lower() in {"1", "true", "yes", "on"}
    return ai_allowed(family) or is_enabled("ai_copilot", family=family)


def answer(*, user, family_id, text: str, language: str = "en", transport=None) -> dict:
    family = Family.objects.filter(id=family_id).first()
    if family is None or not assistant_enabled(family):
        raise ApplicationError(
            "The assistant is available on Premium, or when the ai_copilot flag is on.",
            code="assistant_unavailable",
            status_code=402,
        )
    from apps.assistant.models import Conversation, Message

    conversation = Conversation.objects.create(
        family=family, user=user, language=language, title=text[:80]
    )
    Message.objects.create(conversation=conversation, role="user", content=text)
    transport = transport or HttpClaudeTransport()
    messages = [{"role": "user", "content": text}]
    system = f"{SYSTEM} Reply in {'Hindi' if language.startswith('hi') else 'English'}."
    final = ""
    tools_used = []
    for _turn in range(4):
        result = transport.complete(system=system, messages=messages, tools=TOOL_DEFINITIONS)
        content = result.get("content") or []
        tool_uses = [block for block in content if block.get("type") == "tool_use"]
        text_blocks = [block.get("text", "") for block in content if block.get("type") == "text"]
        if not tool_uses:
            final = "\n".join(text_blocks).strip()
            break
        messages.append({"role": "assistant", "content": content})
        results = []
        for block in tool_uses:
            payload = run_tool(block["name"], block.get("input") or {}, family_id=family_id)
            tools_used.append(block["name"])
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.get("id", block["name"]),
                    "content": json.dumps(payload),
                }
            )
        messages.append({"role": "user", "content": results})
    Message.objects.create(
        conversation=conversation, role="assistant", content=final, tool_calls=tools_used
    )
    return {
        "conversation_id": str(conversation.id),
        "message": final,
        "tools": tools_used,
        "language": language,
    }
