"""Small JSON contracts for coordinator tools; standard library only."""

import json


def obj(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def validate(value, schema, path="arguments"):
    """Validate the small JSON Schema subset declared above, including exact keys."""
    kind = schema["type"]
    if kind == "object":
        if not isinstance(value, dict) or set(value) != set(schema["properties"]):
            raise ValueError(f"{path}: expected exact fields {list(schema['properties'])}")
        for key, subschema in schema["properties"].items():
            validate(value[key], subschema, f"{path}.{key}")
    elif kind == "array":
        if not isinstance(value, list) or len(value) < schema.get("minItems", 0):
            raise ValueError(f"{path}: expected nonempty array")
        for index, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{index}]")
    elif kind == "string":
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{path}: expected nonempty string")
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError(f"{path}: value outside allowed enum")


def parse_arguments(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")

    return json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant)
