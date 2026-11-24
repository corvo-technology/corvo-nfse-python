"""Generate src/corvo_nfse/types/models.py (TypedDicts) from spec/openapi.json.

Run from the repo root: ``python scripts/gen_models.py``. The output is committed; the
contract test (test/test_contract_coverage.py) catches a vendored spec that drifted.
Only the type definitions are generated: the client itself is hand-written.
"""

from __future__ import annotations

import json
import keyword
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "spec" / "openapi.json").read_text())
SCHEMAS: Dict[str, Any] = SPEC["components"]["schemas"]

classes: Dict[str, str] = {}  # name -> source, insertion ordered
aliases: Dict[str, str] = {}


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def literal(values: List[Any]) -> str:
    return (
        "Literal["
        + ", ".join(json.dumps(v) if not isinstance(v, bool) else str(v) for v in values)
        + "]"
    )


def py_type(s: Dict[str, Any], hint: str) -> str:
    """Python annotation (a string, evaluated lazily) for a schema."""
    nullable = bool(s.get("nullable"))
    t = _py_type(s, hint)
    if nullable and not t.startswith("Optional["):
        t = f"Optional[{t}]"
    return t


def _py_type(s: Dict[str, Any], hint: str) -> str:
    if "$ref" in s:
        return ref_name(s["$ref"])
    if "allOf" in s:
        parts = s["allOf"]
        if len(parts) == 1:
            return _py_type(parts[0], hint)
        return "Dict[str, Any]"
    if "oneOf" in s or "anyOf" in s:
        opts = s.get("oneOf") or s.get("anyOf")
        return (
            "Union[" + ", ".join(py_type(o, f"{hint}Variant{i}") for i, o in enumerate(opts)) + "]"
        )
    if "enum" in s:
        return literal(s["enum"])
    t = s.get("type")
    if t == "string":
        return "str"
    if t == "integer":
        return "int"
    if t == "number":
        return "float"
    if t == "boolean":
        return "bool"
    if t == "array":
        return f"List[{py_type(s.get('items', {}), hint + 'Item')}]"
    if t == "object" or "properties" in s:
        if s.get("properties"):
            emit_class(hint, s)
            return hint
        ap = s.get("additionalProperties")
        if isinstance(ap, dict) and ap:
            return f"Dict[str, {py_type(ap, hint + 'Value')}]"
        return "Dict[str, Any]"
    return "Any"


def doc(text: Optional[str], indent: str = "    ") -> str:
    if not text:
        return ""
    text = " ".join(text.split()).replace('"""', "'''").replace("\\", "\\\\")
    lines = textwrap.wrap(text, 96 - len(indent))
    return "\n".join(f"{indent}# {line}" for line in lines) + "\n"


def emit_class(name: str, s: Dict[str, Any], base: Optional[str] = None) -> None:
    props: Dict[str, Any] = s.get("properties", {})
    required = [k for k in s.get("required", []) if k in props]
    optional = [k for k in props if k not in required]

    def body(keys: List[str]) -> str:
        out = ""
        for k in keys:
            out += doc(props[k].get("description"))
            out += f"    {k}: {py_type(props[k], name + k[:1].upper() + k[1:])}\n"
        return out

    parents = base or "TypedDict"
    if any(not k.isidentifier() or keyword.iskeyword(k) for k in props):
        # A key such as "from" is not a Python identifier: use the functional syntax
        # (all keys optional when the class mixes required and optional ones).
        keys = list(props)
        fields = (
            "{"
            + ", ".join(
                f"{json.dumps(k)}: {json.dumps(py_type(props[k], name + k[:1].upper() + k[1:]))}"
                for k in keys
            )
            + "}"
        )
        total = not optional
        classes[name] = f'{name} = TypedDict("{name}", {fields}, total={total})\n'
        return
    summary = " ".join((s.get("description") or "").split())
    docstring = f'    """{summary}"""\n\n' if summary else ""
    if required and optional:
        classes[f"_{name}Required"] = f"class _{name}Required({parents}):\n{body(required)}\n"
        classes[name] = (
            f"class {name}(_{name}Required, total=False):\n{docstring}{body(optional)}\n"
        )
    elif required:
        classes[name] = f"class {name}({parents}):\n{docstring}{body(required)}\n"
    elif optional:
        classes[name] = f"class {name}({parents}, total=False):\n{docstring}{body(optional)}\n"
    else:
        classes[name] = f"class {name}({parents}):\n{docstring}    pass\n\n"


def main() -> None:
    for name, s in SCHEMAS.items():
        if "enum" in s and s.get("type") == "string":
            aliases[name] = literal(s["enum"])
        elif "allOf" in s and len(s["allOf"]) > 1 and "$ref" in s["allOf"][0]:
            base = ref_name(s["allOf"][0]["$ref"])
            extra: Dict[str, Any] = {"properties": {}, "required": []}
            for part in s["allOf"][1:]:
                extra["properties"].update(part.get("properties", {}))
                extra["required"] += part.get("required", [])
            emit_class(name, extra, base=base)
        elif "allOf" in s and len(s["allOf"]) == 1:
            aliases[name] = py_type(s, name)
        elif s.get("type") == "object" and s.get("properties"):
            emit_class(name, s)
        elif "oneOf" in s:
            aliases[name] = py_type(s, name)
        else:
            aliases[name] = py_type(s, name)
    # TypedDict inheritance needs the base defined first.
    order: List[str] = []
    seen = set()

    def visit(n: str) -> None:
        if n in seen or n not in classes:
            return
        seen.add(n)
        header = classes[n].split("\n", 1)[0]
        if header.startswith("class "):
            inside = header[header.index("(") + 1 : header.rindex(")")]
            for p in inside.split(","):
                visit(p.strip())
        order.append(n)

    for n in list(classes):
        visit(n)
    out = '''"""Wire models for the Corvo public API, generated from ``spec/openapi.json`` (contract 0.3.0).

Do not edit by hand: run ``python scripts/gen_models.py``. Field names are the wire names
(camelCase, except billing, schedules and imports, which the API answers in snake_case).
Keys the API may leave out are optional (``total=False``); ``None`` means the API sent ``null``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

'''
    for n in order:
        out += classes[n] + "\n"
    out += "\n"
    for n, a in aliases.items():
        out += f"{n} = {a}\n"
    # Aliases may refer to classes and vice-versa; both are lazy (strings) except these two.
    (ROOT / "src" / "corvo_nfse" / "types" / "models.py").write_text(out.rstrip() + "\n")
    print(f"wrote {len(order)} classes, {len(aliases)} aliases")


main()
