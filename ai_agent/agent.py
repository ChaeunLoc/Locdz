#!/usr/bin/env python3
"""Minimal AI agent CLI with tool-calling support."""

from __future__ import annotations

import ast
import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


SYSTEM_PROMPT = (
    "You are a helpful AI agent. "
    "Use tools when they are useful for the user request. "
    "Keep responses concise and actionable."
)


@dataclass
class AgentConfig:
    api_url: str
    api_key: str
    model: str
    temperature: float = 0.2


class AgentError(Exception):
    """Agent runtime error."""


class LocalTools:
    """Tools exposed to the LLM through function calling."""

    def __init__(self, notes_path: Path) -> None:
        self.notes_path = notes_path
        self.notes_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.notes_path.exists():
            self.notes_path.write_text("[]", encoding="utf-8")

    def get_time(self, timezone_name: str = "UTC") -> dict[str, Any]:
        if timezone_name.upper() == "UTC":
            now = datetime.now(timezone.utc)
            return {"timezone": "UTC", "iso_time": now.isoformat()}
        return {
            "error": (
                "Only UTC is supported in this minimal agent. "
                "Try timezone_name='UTC'."
            )
        }

    def calculate(self, expression: str) -> dict[str, Any]:
        try:
            result = safe_calculate(expression)
            return {"expression": expression, "result": result}
        except Exception as exc:  # pylint: disable=broad-except
            return {"error": f"Invalid expression: {exc}"}

    def save_note(self, note: str) -> dict[str, Any]:
        data = self._read_notes()
        entry = {
            "id": str(uuid.uuid4()),
            "note": note.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        data.append(entry)
        self.notes_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"saved": True, "id": entry["id"]}

    def list_notes(self) -> dict[str, Any]:
        data = self._read_notes()
        return {"count": len(data), "notes": data}

    def _read_notes(self) -> list[dict[str, Any]]:
        raw = self.notes_path.read_text(encoding="utf-8").strip() or "[]"
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise AgentError("notes storage is invalid")
        return parsed

    @staticmethod
    def schema() -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "Get current time in a timezone.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timezone_name": {
                                "type": "string",
                                "description": "IANA timezone name, ex: UTC",
                            }
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Evaluate a basic math expression.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string"},
                        },
                        "required": ["expression"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "save_note",
                    "description": "Save a short note to local memory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note": {"type": "string"},
                        },
                        "required": ["note"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_notes",
                    "description": "List all notes from local memory.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]


def safe_calculate(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Constant,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Unsupported syntax: {type(node).__name__}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError("Only int/float constants are allowed")
    return float(eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, {}))


class AIAgent:
    def __init__(self, config: AgentConfig, tools: LocalTools) -> None:
        self.config = config
        self.tools = tools
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def ask(self, user_text: str, max_rounds: int = 5) -> str:
        self.messages.append({"role": "user", "content": user_text})

        for _ in range(max_rounds):
            message = self._chat_completion(self.messages)
            tool_calls = message.get("tool_calls") or []

            if tool_calls:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": message.get("content") or "",
                        "tool_calls": tool_calls,
                    }
                )
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    raw_args = tool_call["function"].get("arguments") or "{}"
                    tool_args = json.loads(raw_args)
                    tool_result = self._run_tool(tool_name, tool_args)
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(tool_result, ensure_ascii=True),
                        }
                    )
                continue

            content = (message.get("content") or "").strip()
            if not content:
                content = "I could not generate a response."
            self.messages.append({"role": "assistant", "content": content})
            return content

        raise AgentError("Agent exceeded tool loop rounds")

    def _run_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "get_time":
            return self.tools.get_time(args.get("timezone_name", "UTC"))
        if name == "calculate":
            return self.tools.calculate(args["expression"])
        if name == "save_note":
            return self.tools.save_note(args["note"])
        if name == "list_notes":
            return self.tools.list_notes()
        return {"error": f"Unknown tool: {name}"}

    def _chat_completion(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "tools": LocalTools.schema(),
            "tool_choice": "auto",
            "temperature": self.config.temperature,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.config.api_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=90) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise AgentError(f"LLM HTTP error {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise AgentError(f"Cannot reach LLM API: {exc.reason}") from exc

        choices = data.get("choices") or []
        if not choices:
            raise AgentError(f"Invalid LLM response: {data}")
        message = choices[0].get("message") or {}
        if not isinstance(message, dict):
            raise AgentError(f"Unexpected message format: {message}")
        return message


def build_config() -> AgentConfig:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        raise AgentError(
            "Missing LLM_API_KEY. Export it first, then run again.\n"
            "Example:\n"
            "  export LLM_API_KEY='your-key'"
        )
    return AgentConfig(
        api_url=os.getenv(
            "LLM_API_URL", "https://api.openai.com/v1/chat/completions"
        ).strip(),
        api_key=api_key,
        model=os.getenv("LLM_MODEL", "gpt-4o-mini").strip(),
    )


def main() -> int:
    print("Simple AI Agent CLI")
    print("Commands: /help, /exit")
    try:
        config = build_config()
    except AgentError as exc:
        print(f"[config error] {exc}")
        return 1

    notes_path = Path(__file__).with_name("notes.json")
    agent = AIAgent(config=config, tools=LocalTools(notes_path))

    while True:
        try:
            user_input = input("\nYou> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye")
            return 0

        if not user_input:
            continue
        if user_input == "/exit":
            print("Bye")
            return 0
        if user_input == "/help":
            print(
                "Type any request. Examples:\n"
                "- What time is it in UTC?\n"
                "- Calculate: (15 + 5) * 3\n"
                "- Save note: follow up with customer tomorrow"
            )
            continue

        try:
            answer = agent.ask(user_input)
            print(f"Agent> {answer}")
        except AgentError as exc:
            print(f"[agent error] {exc}")
        except json.JSONDecodeError as exc:
            print(f"[agent error] invalid tool call arguments: {exc}")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[agent error] unexpected failure: {exc}")


if __name__ == "__main__":
    sys.exit(main())
