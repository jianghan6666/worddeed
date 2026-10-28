import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agent_system.empirical import coordinator
from agent_system.empirical.demo import DemoProvider
from agent_system.empirical.workflow import Workflow, write_json
from agent_system.providers import ResponsesProvider


def reply(output, **updates):
    return {"id": "fixture-response", "status": "completed", "model": None,
            "usage": None, "output": output, "fixture": True, **updates}


def call(name, arguments=None, call_id="test-call"):
    return {"type": "function_call", "call_id": call_id, "name": name,
            "arguments": json.dumps(arguments or {})}


class SequenceProvider:
    mode = "offline_fixture"
    requested_model = None
    requested_effort = None

    def __init__(self, *replies):
        self.replies = iter(replies)

    def respond(self, *args):
        return next(self.replies)


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        packages = self.root / "packages"
        for name, inventory in (("step3_risk_score_collaborator_20261027", "MANIFEST.json"),
                                ("step4_full_from_raw_20261027", "manifest.json")):
            write_json(packages / name / inventory, {"fixture": True})
        self.config = {"profile": "reproduce", "packages_root": str(packages),
                       "python": "/unused", "demonstration": True,
                       "coordinator": {"model": "gpt-6.1-sol", "effort": "high"}}
        self.workflow = Workflow(self.config, self.root / "run")
        self.executed = []

    def worker(self, command, **kwargs):
        request = json.loads(Path(command[-2]).read_text())
        self.executed.append(request["stage"])
        artifact = Path(request["out"]) / "fixture.json"
        write_json(artifact, {"demonstration": True, "stage": request["stage"]})
        write_json(command[-1], {"fixture": str(artifact), "demonstration": True})

    def test_same_dispatcher_and_through_status_are_authoritative(self):
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.worker):
            summary = coordinator.run(self.workflow, "step2", DemoProvider())
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(self.executed, ["step1", "step2"])
        self.assertTrue(summary["workflow"]["through_complete"])
        self.assertEqual(summary["workflow"]["status"], "ready")
        self.assertFalse(summary["scientific_completion"])
        state = json.loads((self.workflow.out / "coordinator.json").read_text())
        self.assertEqual(state["settings"], self.config["coordinator"])
        self.assertTrue(any(i.get("type") == "function_call_output" for i in state["history"]))
        events = [json.loads(s) for s in (self.workflow.out / "events.jsonl").read_text().splitlines()]
        self.assertTrue({"coordinator_request", "coordinator_reply", "coordinator_tool_receipt"} <= {e["event"] for e in events})
        # Finishing a partial target does not prevent a later explicit extension.
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.worker):
            extended = coordinator.run(Workflow(self.config, self.workflow.out), "step3", DemoProvider())
        self.assertEqual(extended["status"], "completed")
        self.assertEqual(self.executed, ["step1", "step2", "step3"])

    def test_premature_finish_and_prose_do_not_complete(self):
        result = coordinator.run(self.workflow, provider=SequenceProvider(reply([call("finish")])))
        self.assertEqual(result["status"], "invalid_output")
        self.assertIn("before", result["result"]["reason"])
        other = Workflow(self.config, self.root / "prose")
        result = coordinator.run(other, provider=SequenceProvider(reply([
            {"type": "message", "content": [{"type": "output_text", "text": "All stages complete!"}]}])))
        self.assertEqual(result["status"], "incomplete")
        self.assertFalse(result["workflow"]["through_complete"])

    def test_unknown_out_of_order_extra_arguments_and_parallel_calls_rejected(self):
        cases = [
            [call("read_file", {"path": "/etc/passwd"})],
            [call("run_stage", {"stage": "step3"})],
            [call("get_status", {"path": "other"})],
            [call("run_stage", {"stage": "step4"})],  # Beyond step2 target.
            [call("read_result", {"stage": "step1"})],
            [call("get_status"), call("run_stage", {"stage": "step1"}, "second")],
        ]
        for index, output in enumerate(cases):
            with self.subTest(index=index), patch("agent_system.empirical.workflow.subprocess.run") as worker:
                workflow = Workflow(self.config, self.root / f"invalid-{index}")
                result = coordinator.run(workflow, "step2", SequenceProvider(reply(output)))
                self.assertEqual(result["status"], "invalid_output")
                worker.assert_not_called()

    def test_completed_stage_without_tool_receipt_is_not_executed_again(self):
        dispatch = coordinator._dispatch
        interrupted = False

        def crash_after_completion(workflow, through, name, arguments):
            nonlocal interrupted
            result = dispatch(workflow, through, name, arguments)
            if name == "run_stage" and arguments["stage"] == "step2" and not interrupted:
                interrupted = True
                raise KeyboardInterrupt()
            return result

        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.worker), \
             patch.object(coordinator, "_dispatch", side_effect=crash_after_completion):
            summary = coordinator.run(self.workflow, "step3", DemoProvider())
        self.assertEqual(summary["status"], "interrupted")
        state = json.loads((self.workflow.out / "coordinator.json").read_text())
        self.assertEqual(state["pending_call"]["name"], "run_stage")
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.worker):
            summary = coordinator.run(Workflow(self.config, self.workflow.out), "step3", DemoProvider())
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(self.executed, ["step1", "step2", "step3"])
        self.assertEqual(self.workflow.state["stages"]["step2"]["attempt"], 1)

    def test_completed_resume_verifies_artifacts_before_returning(self):
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.worker):
            coordinator.run(self.workflow, "step1", DemoProvider())
        artifact = self.workflow.out / "step1/fixture.json"
        artifact.write_text("changed")
        with self.assertRaisesRegex(ValueError, "output changed"):
            coordinator.run(self.workflow, "step1", DemoProvider())

    def test_transport_failure_is_checkpointed_and_resumable(self):
        provider = DemoProvider()
        with patch.object(provider, "respond", side_effect=ConnectionError("private error text")):
            result = coordinator.run(self.workflow, "step1", provider)
        self.assertEqual(result["status"], "transport_failed")
        self.assertNotIn("private error text", json.dumps(result))
        self.assertEqual(result["usage_status"], "unknown_after_failed_request")
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.worker):
            result = coordinator.run(self.workflow, "step1", provider)
        self.assertEqual(result["status"], "completed")

    def test_refusal_incomplete_and_malformed_reply_execute_nothing(self):
        responses = [
            reply([{"type": "message", "content": [{"type": "refusal", "refusal": "No"}]}]),
            reply([call("run_stage", {"stage": "step1"})], status="incomplete"),
            reply([None]),
            reply([call("get_status"), {"type": "unknown"}]),
        ]
        with patch("agent_system.empirical.workflow.subprocess.run") as worker:
            for index, response in enumerate(responses):
                workflow = Workflow(self.config, self.root / f"bad-{index}")
                result = coordinator.run(workflow, provider=SequenceProvider(response))
                self.assertNotEqual(result["status"], "completed")
            worker.assert_not_called()

    def test_responses_effort_and_opaque_reasoning_are_preserved(self):
        requests = []
        reasoning = {"type": "reasoning", "content": None, "summary": [], "encrypted_content": "fixture-opaque"}
        replies = iter([reply([reasoning, call("get_status")]), reply([])])

        def create(**kwargs):
            requests.append(copy.deepcopy(kwargs))
            data = next(replies)
            return SimpleNamespace(model_dump=lambda **_: data, _request_id="fixture-request")

        client = SimpleNamespace(responses=SimpleNamespace(create=create))
        provider = ResponsesProvider("fixture-model", client=client, effort="high")
        result = coordinator.run(self.workflow, provider=provider)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(requests[0]["reasoning"], {"effort": "high"})
        self.assertIn(reasoning, requests[1]["input"])
        self.assertFalse(requests[0]["parallel_tool_calls"])
        self.assertEqual(result["coordinator"]["requested_effort"], "high")
        self.assertEqual(result["coordinator"]["last_response"]["request_id"], "fixture-request")


if __name__ == "__main__":
    unittest.main()
