# Callable tools

The [coordinator](../../agent_system/empirical/coordinator.py) calls four tools: `get_status`, `run_stage`, `read_result`, and `finish`. The [dispatcher](../../agent_system/empirical/workflow.py) enforces order, saves results, and verifies completed artifacts on resume.

| Stage | Implementation | Output |
| --- | --- | --- |
| Topic preparation | [step1.py](../../agent_system/empirical/step1.py) | Bound catalogue and topic-density inputs |
| Independent screening | [screening.py](../../agent_system/empirical/screening.py) | Literal reader responses, selected topics, reasons and minority votes |
| Proxy estimation | [step3.py](../../agent_system/empirical/step3.py) | Scores and model receipts from compatible study programs |
| Downstream analysis | [step4.py](../../agent_system/empirical/step4.py) | Matched inputs, estimation records and tables |
| Offline demonstration | [demo.py](../../agent_system/empirical/demo.py) | Invented inputs exercising handoffs and resume |

Computational programs and empirical inputs are supplied through explicit local configuration. See the [runtime guide](../../agent_system/empirical/README.md) for setup and input contracts.
