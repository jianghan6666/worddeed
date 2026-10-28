"""A lean Responses loop over the durable Workflow; no separate stage engine."""

import json
import uuid

from agent_system.contracts import enum, obj, parse_arguments, validate
from agent_system.providers import ResponsesProvider
from agent_system.runtime import output_problem
from .workflow import STAGES, write_json

SCHEMAS = {
    "get_status": obj({}),
    "run_stage": obj({"stage": enum(*STAGES)}),
    "read_result": obj({"stage": enum(*STAGES)}),
    "finish": obj({}),
}
DESCRIPTIONS = {
    "get_status": "Inspect authoritative workflow status and the requested stopping stage.",
    "run_stage": "Run one configured stage in order; completed artifacts are verified and reused.",
    "read_result": "Read a completed stage's actual, hash-verified artifact references.",
    "finish": "Finish only when all stages through the requested stage actually completed.",
}
TOOLS = [{"type": "function", "name": name, "description": DESCRIPTIONS[name],
          "parameters": schema, "strict": True} for name, schema in SCHEMAS.items()]
INSTRUCTIONS = """Coordinate the configured empirical workflow using only the supplied tools.
First inspect status. Run stages sequentially through the requested stopping stage,
read their actual results, and finish. Preserve all scientific inputs and historical
trials. Do not invent results, change configuration, execute arbitrary code, or claim
scientific validity. Tool status and saved artifacts determine completion; your prose
cannot. If demonstration is true, every result is a synthetic demonstration fixture,
not a scientific result, model judgment, trained score, or empirical estimate.
"""
DEFAULT_COORDINATOR = {"model": "gpt-6.1-sol", "effort": "high"}


def _status(workflow, through):
    required = STAGES[:STAGES.index(through) + 1]
    status = workflow.status()
    complete = all(status["stages"].get(s) == "complete" for s in required)
    # Workflow verifies the actual output hashes even on a completed run.
    for stage in required:
        if status["stages"].get(stage) == "complete":
            workflow.run_stage(stage)
    return {**status, "through": through, "through_complete": complete,
            "demonstration": bool(workflow.config.get("demonstration", False)),
            "scientific_completion": False}


def _dispatch(workflow, through, name, arguments):
    if name not in SCHEMAS:
        raise ValueError(f"Tool {name!r} is not allowed for coordinator")
    validate(arguments, SCHEMAS[name])
    if name == "get_status":
        return {"status": "ok", "workflow": _status(workflow, through)}
    if name in {"run_stage", "read_result"}:
        stage = arguments["stage"]
        if STAGES.index(stage) > STAGES.index(through):
            raise ValueError("Stage exceeds the requested stopping stage")
        if name == "read_result" and workflow.status()["stages"].get(stage) != "complete":
            raise ValueError("No completed result exists for this stage")
        return {"status": "ok", "stage": stage, "artifacts": workflow.run_stage(stage),
                "demonstration": bool(workflow.config.get("demonstration", False)),
                "scientific_completion": False}
    status = _status(workflow, through)
    if not status["through_complete"]:
        raise ValueError("Cannot finish before the requested stages complete")
    return {"status": "ok", "workflow": status}


def run(workflow, through="step4", provider=None):
    """Run/resume one coordinator conversation; model narration is never authority.

    ``coordinator.json`` checkpoints history and an outstanding request/call.
    ``events.jsonl`` retains requests, replies and tool receipts. A crash between a
    stage completion and its receipt replays the same call through Workflow, whose
    completed-stage path verifies artifacts without rerunning the numerical worker.
    Failed or interrupted stages may be retried by a resumed conversation.
    """
    if through not in STAGES:
        raise ValueError(f"Unknown stage: {through}")
    path = workflow.out / "coordinator.json"
    settings = {**DEFAULT_COORDINATOR, **workflow.config.get("coordinator", {})}
    state = json.loads(path.read_text()) if path.exists() else {
        "through": through, "settings": settings, "status": "ready",
        "history": [{"role": "user", "content": f"Run the configured workflow through {through}. "
                     f"Demonstration={bool(workflow.config.get('demonstration', False))}."}],
        "pending_call": None, "pending_request": None, "last_response": None,
    }
    if state["settings"] != settings:
        raise ValueError("Coordinator model/effort changed; use a new run directory")
    if state["through"] != through:
        if state["pending_call"] or STAGES.index(through) < STAGES.index(state["through"]):
            raise ValueError("Cannot shorten or change an outstanding coordinator target")
        state["history"].append({"role": "user", "content": f"Continue through {through}."})
        state.update(through=through, status="ready")
    if state["status"] == "completed":
        status = _status(workflow, through)
        if status["through_complete"]:
            return state["summary"]
    provider = provider if provider is not None else ResponsesProvider(settings["model"], effort=settings["effort"])
    identity = {"mode": provider.mode, "requested_model": getattr(provider, "requested_model", None),
                "requested_effort": getattr(provider, "requested_effort", None)}
    if state.get("provider") and state["provider"] != identity:
        raise ValueError("Coordinator provider changed; use a new run directory")
    state["provider"] = identity

    def checkpoint():
        write_json(path, state)

    def finish(status, **details):
        actual = _status(workflow, through)
        summary = {"status": status, "through": through, "workflow": actual,
                   "demonstration": actual["demonstration"], "scientific_completion": False,
                   "coordinator": {"configured": settings, **identity,
                                   "last_response": state.get("last_response")},
                   "checkpoint": str(path), **details}
        state.update(status=status, summary=summary)
        checkpoint()
        workflow.event("coordinator_finished", summary=summary)
        return summary

    checkpoint()
    try:
        while True:
            call = state["pending_call"]
            if call is not None:
                try:
                    result = _dispatch(workflow, through, call["name"], parse_arguments(call["arguments"]))
                except (ValueError, KeyError, TypeError) as exc:
                    result = {"status": "invalid_output", "reason": str(exc)}
                except Exception as exc:
                    # Preserve exception identity; worker diagnostics live in stage logs.
                    result = {"status": "tool_failed", "error_type": type(exc).__name__}
                receipt = {"type": "function_call_output", "call_id": call["call_id"],
                           "output": json.dumps(result, ensure_ascii=False, allow_nan=False)}
                state["history"].append(receipt)
                state["pending_call"] = None
                checkpoint()
                workflow.event("coordinator_tool_receipt", call=call, receipt=receipt)
                if result["status"] != "ok":
                    return finish(result["status"], failed_tool=call["name"], result=result)
                if call["name"] == "finish":
                    return finish("completed")
                continue
            # An interrupted transport can be requested again; there are no stage
            # side effects until a fully validated reply has been checkpointed.
            request_id = uuid.uuid4().hex
            state["pending_request"] = request_id
            state["status"] = "running"
            checkpoint()
            workflow.event("coordinator_request", attempt=request_id, provider=identity,
                           configured=settings, instructions=INSTRUCTIONS, tools=TOOLS, input=state["history"])
            try:
                reply = provider.respond("coordinator", INSTRUCTIONS, TOOLS, state["history"])
            except Exception as exc:
                return finish("transport_failed", error_type=type(exc).__name__,
                              request_id=getattr(exc, "request_id", None),
                              usage_status="unknown_after_failed_request")
            state["pending_request"] = None
            workflow.event("coordinator_reply", attempt=request_id, response=reply)
            if not isinstance(reply, dict):
                return finish("invalid_output", reason="Provider response must be an object")
            state["last_response"] = {
                "response_id": reply.get("id"), "request_id": reply.get("transport_request_id"),
                "returned_model": reply.get("model"), "usage": reply.get("usage"),
                "usage_status": "reported" if reply.get("usage") is not None else
                    ("not_applicable_fixture_no_api_call" if reply.get("fixture") else "missing_from_response"),
            }
            output = reply.get("output", [])
            problem = output_problem(output, state["history"])
            if problem:
                return finish("invalid_output", reason=problem)
            refusal = any(part.get("type") == "refusal" for item in output
                          for part in (item.get("content") or []) if isinstance(part, dict))
            if refusal or reply.get("status") != "completed":
                return finish("refused" if refusal else "incomplete", provider_status=reply.get("status"))
            calls = [item for item in output if item.get("type") == "function_call"]
            if len(calls) > 1:
                return finish("invalid_output", reason="Expected one sequential tool call")
            state["history"].extend(output)  # Includes opaque encrypted reasoning.
            state["pending_call"] = calls[0] if calls else None
            checkpoint()  # Reply and pending call durable before any tool side effect.
            if not calls:
                narration = [p["text"] for item in output for p in (item.get("content") or [])
                             if isinstance(p, dict) and p.get("type") == "output_text"]
                return finish("completed" if _status(workflow, through)["through_complete"] else "incomplete",
                              model_narration=narration)
    except KeyboardInterrupt:
        return finish("interrupted")
