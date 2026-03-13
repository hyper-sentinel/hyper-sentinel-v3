"""
Tool Registry — Auto-schema generation from typed Python functions.

Replaces the manual TOOLS_SPEC[] + execute_tool() pattern with introspection.
Functions with type hints and docstrings auto-generate JSON schemas.

Usage:
    registry = ToolRegistry()
    registry.register(get_crypto_price, aster_ticker, ...)
    registry.register(my_func, name="custom_tool_name")  # alias

    # Provider-specific formats
    anthropic_tools = registry.for_anthropic()
    openai_tools = registry.for_openai()

    # Execute by name
    result = registry.execute("get_crypto_price", {"coin_id": "bitcoin"})
"""

import inspect
import json
import traceback
from typing import Any, Callable, Optional, get_type_hints


# ── Type → JSON Schema mapping ──────────────────────────────

_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _python_type_to_json(annotation) -> str:
    """Convert a Python type annotation to a JSON Schema type string."""
    # Handle Optional[X] → X (already handled as nullable)
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        # typing.Optional[X] = Union[X, None]
        args = getattr(annotation, "__args__", ())
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _python_type_to_json(non_none[0])
        return "string"

    return _TYPE_MAP.get(annotation, "string")


def _build_schema(func: Callable) -> dict:
    """Build a JSON Schema 'parameters' object from function signature + type hints."""
    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    properties: dict[str, dict] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        prop: dict[str, Any] = {}

        # Type
        if param_name in hints:
            ann = hints[param_name]
            prop["type"] = _python_type_to_json(ann)

            # Check if Optional
            origin = getattr(ann, "__origin__", None)
            if origin is not None:
                args = getattr(ann, "__args__", ())
                if type(None) in args:
                    # It's Optional — not required
                    pass
        else:
            prop["type"] = "string"

        # Default value
        if param.default is not inspect.Parameter.empty:
            prop["default"] = param.default
        else:
            # No default = required (unless Optional type)
            origin = getattr(hints.get(param_name), "__origin__", None)
            is_optional = False
            if origin is not None:
                args = getattr(hints.get(param_name), "__args__", ())
                is_optional = type(None) in args
            if not is_optional:
                required.append(param_name)

        properties[param_name] = prop

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _extract_description(func: Callable) -> str:
    """Extract the first line of a function's docstring as its description."""
    doc = inspect.getdoc(func) or ""
    # Use first line only for the tool description
    return doc.split("\n")[0].strip() if doc else f"Tool: {func.__name__}"


class ToolRegistry:
    """Registry of tools with auto-generated schemas and dispatch."""

    def __init__(self):
        self._tools: dict[str, dict] = {}  # name -> {func, schema, description}

    def register(self, *funcs: Callable, **named: Callable) -> "ToolRegistry":
        """Register functions as tools.

        Positional args: register under the function's own name.
        Keyword args: register under the given alias.

        Examples:
            registry.register(aster_ticker, aster_balance)
            registry.register(get_aster_ticker=aster_ticker)
        """
        for func in funcs:
            name = func.__name__
            self._tools[name] = {
                "func": func,
                "schema": _build_schema(func),
                "description": _extract_description(func),
            }

        for alias, func in named.items():
            self._tools[alias] = {
                "func": func,
                "schema": _build_schema(func),
                "description": _extract_description(func),
            }

        return self

    def register_custom(
        self,
        name: str,
        func: Callable,
        description: str | None = None,
        schema: dict | None = None,
    ) -> "ToolRegistry":
        """Register a tool with explicit schema override (for complex/special tools)."""
        self._tools[name] = {
            "func": func,
            "schema": schema or _build_schema(func),
            "description": description or _extract_description(func),
        }
        return self

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    # ── Provider Formats ──────────────────────────────────────

    def specs(self) -> list[dict]:
        """Return tool specs in the neutral format (same as old TOOLS_SPEC)."""
        return [
            {
                "name": name,
                "description": t["description"],
                "parameters": t["schema"],
            }
            for name, t in self._tools.items()
        ]

    def for_anthropic(self) -> list[dict]:
        """Anthropic format: name + description + input_schema."""
        return [
            {
                "name": name,
                "description": t["description"],
                "input_schema": t["schema"],
            }
            for name, t in self._tools.items()
        ]

    def for_openai(self) -> list[dict]:
        """OpenAI/Gemini/Grok format: type=function + function={name, description, parameters}."""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": t["description"],
                    "parameters": t["schema"],
                },
            }
            for name, t in self._tools.items()
        ]

    # ── Execution ─────────────────────────────────────────────

    def execute(self, name: str, args: dict) -> str:
        """Execute a tool by name, return JSON string result."""
        tool = self._tools.get(name)
        if not tool:
            return json.dumps({"error": f"Unknown tool: {name}"})

        try:
            func = tool["func"]
            sig = inspect.signature(func)

            # Only pass args that the function accepts
            valid_params = set(sig.parameters.keys())
            filtered = {k: v for k, v in args.items() if k in valid_params}

            result = func(**filtered)
            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            return json.dumps({"error": str(e), "traceback": traceback.format_exc()})
