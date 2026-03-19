"""
Custom test suite loader — parses and validates user-uploaded Python test files.

Security model
--------------
We run AST analysis before exec() to block dangerous imports and builtins.
Allowed imports are an explicit allowlist (not a blocklist) to be safe.
The exec namespace is also stripped of dangerous builtins at runtime.
"""
import ast
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

# Only these stdlib modules are allowed in custom test files
_ALLOWED_IMPORTS = {
    "re", "json", "math", "typing", "dataclasses",
    "datetime", "string", "random", "collections", "itertools",
}

_BLOCKED_BUILTINS = frozenset({
    # Code execution
    "exec", "eval", "compile", "__import__",
    # I/O and system access
    "open", "input", "breakpoint",
    # Introspection that enables sandbox escapes
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "hasattr", "delattr",
    "type", "object",
})


class CustomSuiteValidationError(ValueError):
    """Raised when a custom test file fails validation."""


def _validate_ast(source: str) -> None:
    """Walk the AST and raise CustomSuiteValidationError on dangerous constructs."""
    try:
        tree = ast.parse(source, filename="<custom_suite>")
    except SyntaxError as e:
        raise CustomSuiteValidationError(f"Syntax error in test file: {e}") from e

    for node in ast.walk(tree):
        # Block any imports not in the allowlist
        if isinstance(node, ast.Import):
            for alias in node.names:
                pkg = alias.name.split(".")[0]
                if pkg not in _ALLOWED_IMPORTS:
                    raise CustomSuiteValidationError(
                        f"Import '{alias.name}' is not allowed. "
                        f"Allowed imports: {sorted(_ALLOWED_IMPORTS)}"
                    )
        elif isinstance(node, ast.ImportFrom):
            pkg = (node.module or "").split(".")[0]
            if pkg and pkg not in _ALLOWED_IMPORTS:
                raise CustomSuiteValidationError(
                    f"Import from '{node.module}' is not allowed. "
                    f"Allowed imports: {sorted(_ALLOWED_IMPORTS)}"
                )

        # Block dangerous built-in calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _BLOCKED_BUILTINS:
                raise CustomSuiteValidationError(
                    f"Built-in '{node.func.id}()' is not allowed in test files."
                )

        # Block dunder attribute access — primary sandbox escape vector
        # e.g. obj.__class__.__bases__[0].__subclasses__()
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__"):
                raise CustomSuiteValidationError(
                    f"Dunder attribute access ('{node.attr}') is not allowed in test files."
                )


def _safe_exec(source: str) -> dict[str, Any]:
    """Execute the source in a restricted namespace and return it."""
    # Strip dangerous builtins from the __builtins__ available to the file
    import builtins
    safe_builtins = {
        k: v for k, v in vars(builtins).items()
        if k not in _BLOCKED_BUILTINS
    }
    namespace: dict[str, Any] = {"__builtins__": safe_builtins}
    exec(compile(source, "<custom_suite>", "exec"), namespace)  # noqa: S102
    return namespace


def _normalise_test(raw: Any, idx: int) -> dict[str, Any]:
    """Coerce a raw test dict into the canonical AgentProbe test case format."""
    if not isinstance(raw, dict):
        raise CustomSuiteValidationError(
            f"TESTS[{idx}] must be a dict, got {type(raw).__name__}"
        )
    if not raw.get("input") and raw.get("input") != "":
        raise CustomSuiteValidationError(
            f"TESTS[{idx}] is missing required field 'input'"
        )
    return {
        "id": str(raw.get("id") or f"custom_{uuid.uuid4().hex[:6]}"),
        "category": str(raw.get("category", "custom")),
        "subcategory": str(raw.get("subcategory", "")),
        "input": str(raw.get("input", "")),
        "expected_behavior": str(raw.get("expected_behavior", "")),
        "difficulty": str(raw.get("difficulty", "medium")),
        "tags": list(raw.get("tags") or []),
        "metadata": {k: v for k, v in raw.items()
                     if k not in {"id", "category", "subcategory", "input",
                                  "expected_behavior", "difficulty", "tags"}},
    }


def load_custom_suite(source: str) -> dict[str, Any]:
    """
    Validate and parse a custom test suite Python file.

    Returns a dict with:
        suite_name   str
        description  str
        tests        list[dict]   — normalised test cases

    Raises CustomSuiteValidationError on any validation failure.
    """
    _validate_ast(source)

    namespace = _safe_exec(source)

    suite_name = str(namespace.get("SUITE_NAME") or "custom").strip()
    description = str(namespace.get("DESCRIPTION") or "").strip()
    raw_tests = namespace.get("TESTS")

    if not isinstance(raw_tests, list):
        raise CustomSuiteValidationError(
            "TESTS must be defined as a list at module level."
        )
    if not raw_tests:
        raise CustomSuiteValidationError("TESTS list is empty.")
    if len(raw_tests) > 500:
        raise CustomSuiteValidationError(
            f"TESTS list has {len(raw_tests)} items — maximum is 500."
        )

    tests = [_normalise_test(t, i) for i, t in enumerate(raw_tests)]
    categories = sorted({t["category"] for t in tests})

    logger.info(
        "Loaded custom suite '%s': %d tests across categories %s",
        suite_name, len(tests), categories,
    )
    return {
        "suite_name": suite_name,
        "description": description,
        "tests": tests,
        "categories": categories,
    }
