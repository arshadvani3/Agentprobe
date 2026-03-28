"""
Custom test suite loader — parses and validates user-uploaded Python test files.

Security model
--------------
Two-layer defence:
1. AST pre-validation — blocks dangerous imports and dunder attribute access before
   any code is compiled (fast, catches obvious attacks).
2. RestrictedPython execution — compiles to bytecode that inserts _getattr_, _getiter_,
   _getitem_, _write_ guards at every attribute access and assignment. Even if the AST
   check is bypassed, the runtime guards prevent sandbox escapes.
"""
import ast
import builtins as _builtins_module
import logging
import uuid
from typing import Any

from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import safe_builtins, guarded_iter_unpack_sequence

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


def _make_restricted_import():
    """Return a __import__ that only allows modules in _ALLOWED_IMPORTS."""
    def _restricted_import(name: str, *args: Any, **kwargs: Any) -> Any:
        pkg = name.split(".")[0]
        if pkg not in _ALLOWED_IMPORTS:
            raise ImportError(
                f"Import of '{name}' is not allowed in test files. "
                f"Allowed imports: {sorted(_ALLOWED_IMPORTS)}"
            )
        return _builtins_module.__import__(name, *args, **kwargs)
    return _restricted_import


def _safe_exec(source: str) -> dict[str, Any]:
    """
    Execute the source inside a RestrictedPython sandbox and return the local namespace.

    RestrictedPython rewrites the bytecode to insert _getattr_, _getiter_, _getitem_,
    and _write_ guards on every attribute access, iteration, and assignment — preventing
    sandbox escape via subclass traversal or attribute manipulation even if the AST
    pre-check is somehow bypassed.
    """
    try:
        byte_code = compile_restricted(source, "<custom_suite>", "exec")
    except SyntaxError as exc:
        raise CustomSuiteValidationError(f"Syntax error in test file: {exc}") from exc

    restricted_globals: dict[str, Any] = {
        **safe_globals,
        "__builtins__": {
            **safe_builtins,
            "__import__": _make_restricted_import(),
        },
        "_getiter_": iter,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
    }
    local_ns: dict[str, Any] = {}
    try:
        exec(byte_code, restricted_globals, local_ns)  # noqa: S102
    except (ImportError, NameError, TypeError) as exc:
        raise CustomSuiteValidationError(f"Error executing test file: {exc}") from exc
    return local_ns


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
