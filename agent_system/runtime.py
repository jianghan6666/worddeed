"""Validate model replies before dispatching tools."""

def output_problem(output, history):
    """Check a whole reply before executing any calls from it."""
    if not isinstance(output, list) or any(not isinstance(item, dict) for item in output):
        return "Response output must be a list of objects"
    old_ids = {item["call_id"] for item in history if item.get("type") == "function_call"}
    for item in output:
        kind = item.get("type")
        if kind not in {"function_call", "message", "reasoning"}:
            return "Unsupported or absent response item type"
        if item.get("status") in {"in_progress", "incomplete"}:
            return "Incomplete output item in a completed response"
        if kind == "function_call":
            if any(not isinstance(item.get(key), str) or not item[key].strip()
                   for key in ("call_id", "name", "arguments")):
                return "Function call requires nonempty call_id, name and JSON arguments"
            if item["call_id"] in old_ids:
                return "Duplicate function call_id"
            old_ids.add(item["call_id"])
        if kind == "message":
            content = item.get("content")
            if not isinstance(content, list) or any(not isinstance(part, dict) for part in content):
                return "Message content must be a list of objects"
            for part in content:
                key = {"output_text": "text", "refusal": "refusal"}.get(part.get("type"))
                if key is None or not isinstance(part.get(key), str):
                    return "Malformed message content"
    return None
