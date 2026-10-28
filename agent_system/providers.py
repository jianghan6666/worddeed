"""Optional Responses API provider for the connected workflow."""

import os


class ResponsesProvider:
    mode = "live_openai"

    def __init__(self, model, client=None, *, effort=None):
        if not model or not model.strip():
            raise ValueError("Live mode requires an explicit --model; no model is chosen by default")
        self.requested_model = model
        self.requested_effort = effort
        if client is None:
            if not os.environ.get("OPENAI_API_KEY"):
                raise ValueError("Live mode requires OPENAI_API_KEY")
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError("Optional dependency missing: install openai for live mode") from exc
            # No silent provider retries or altered elicitation paths.
            client = OpenAI(max_retries=0)
        self.client = client

    def respond(self, role, instructions, tools, history):
        reasoning = {"reasoning": {"effort": self.requested_effort}} if self.requested_effort is not None else {}
        response = self.client.responses.create(
            model=self.requested_model, instructions=instructions, tools=tools,
            input=history, store=False, include=["reasoning.encrypted_content"],
            parallel_tool_calls=False,
            **reasoning,
        )
        data = response.model_dump(mode="json")
        data["transport_request_id"] = getattr(response, "_request_id", None)
        return data
