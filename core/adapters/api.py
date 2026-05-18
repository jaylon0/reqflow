"""APIAdapter - model adapter for API-based runtimes (OpenAI, Anthropic, Gemini)."""

from __future__ import annotations

import json
import os
from typing import Any

from .base import ModelAdapter, ModelResponse, ToolResult, ToolCall, TokenUsage


class APIAdapter(ModelAdapter):
    """Adapter that calls models via HTTP API.

    Supports OpenAI-compatible APIs (OpenAI, Anthropic via proxy, Gemini, DeepSeek).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o",
        provider: str = "openai",
    ):
        self.api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY", "")
        self.base_url = base_url or self._default_base_url(provider)
        self.model = model
        self.provider = provider

    @classmethod
    def from_config(cls, config: "RuntimeConfig") -> "APIAdapter":
        """Create APIAdapter from RuntimeConfig."""
        api_key = config.api_key
        if not api_key and config.env_key:
            api_key = os.environ.get(config.env_key, "")
        return cls(
            api_key=api_key,
            base_url=config.api_base,
            model=config.model or "gpt-4o",
            provider=config.name,
        )

    @property
    def name(self) -> str:
        return f"api_{self.provider}"

    def _default_base_url(self, provider: str) -> str:
        urls = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1beta",
            "deepseek": "https://api.deepseek.com/v1",
        }
        return urls.get(provider, urls["openai"])

    def call(
        self,
        prompt: str,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Call the model via API.

        Note: This is a synchronous implementation using urllib.
        For production use, consider using httpx or aiohttp.
        """
        import urllib.request

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_content = ""
        if context:
            user_content += f"[Context]\n{context}\n\n"
        user_content += prompt
        messages.append({"role": "user", "content": user_content})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        # Add tools if available (function calling)
        if tools:
            functions = self._tools_to_functions(tools)
            if functions:
                payload["tools"] = [{"type": "function", "function": f} for f in functions]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # Anthropic uses different header
        if self.provider == "anthropic":
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            payload = self._convert_to_anthropic_format(payload)

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"API call failed: {e}") from e

        return self._parse_response(result)

    def _tools_to_functions(self, tools: list[str]) -> list[dict[str, Any]]:
        """Convert canonical tool names to function definitions."""
        from ..tool_bridge import CANONICAL_TOOLS

        functions = []
        for tool_name in tools:
            if tool_name in CANONICAL_TOOLS:
                tool_def = CANONICAL_TOOLS[tool_name]
                functions.append({
                    "name": tool_name,
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"],
                })
        return functions

    def _convert_to_anthropic_format(self, payload: dict) -> dict:
        """Convert OpenAI format to Anthropic format."""
        messages = payload.get("messages", [])
        system = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                anthropic_messages.append(msg)

        result = {
            "model": payload.get("model", self.model),
            "max_tokens": 4096,
            "messages": anthropic_messages,
        }
        if system:
            result["system"] = system
        return result

    def _parse_response(self, result: dict) -> ModelResponse:
        """Parse API response into ModelResponse."""
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})

        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                arguments=args,
            ))

        usage = result.get("usage", {})
        tokens = TokenUsage(
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )

        return ModelResponse(
            content=message.get("content", ""),
            tool_calls=tool_calls,
            tokens=tokens,
            raw=result,
        )

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        """Execute a tool locally (API adapter runs tools on the host)."""
        import subprocess

        if tool_name == "bash":
            try:
                result = subprocess.run(
                    args.get("command", ""),
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=args.get("timeout", 120000) / 1000,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr if result.returncode != 0 else None,
                )
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))

        elif tool_name in ("read_file", "edit_file", "write_file"):
            # File operations need to be handled by the caller
            return ToolResult(
                success=True,
                output=f"File operation {tool_name} delegated to host",
                raw={"tool": tool_name, "args": args},
            )

        return ToolResult(
            success=False,
            output="",
            error=f"Tool {tool_name} not supported in API mode",
        )

    def supports_capability(self, capability: str) -> bool:
        """API adapter capabilities depend on the model."""
        capabilities = {
            "agent_tools": False,  # No native agent tools
            "bash": True,  # Can run via subprocess
            "file_edit": False,  # Needs host integration
            "image": self.provider in ("openai", "gemini"),
            "parallel": False,
        }
        return capabilities.get(capability, False)
