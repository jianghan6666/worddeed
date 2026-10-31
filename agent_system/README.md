# AI Microfoundation Proxy runtime

The runtime connects coordinator decisions, computational stages and saved evidence. Start with the [runtime guide](empirical/README.md) for the offline demo, state/resume, tests and current empirical execution.

`contracts.py`, `providers.py` and `runtime.py` provide argument checks, provider handling and reply validation. `empirical/` contains the connected workflow and its current stage adapters. The coordinator, handoff and persistence patterns are reusable; the numerical adapters implement the CEO/R&D application and retain its specific input contracts and scientific programs.

The [CEO application](../applications/ceo-risk-preference/README.md) owns the scientific materials, full results and replication evidence. Developing another application requires explicit scientific choices and compatible adapters, as described in [Adding an application](../docs/NEW_APPLICATION.md). A general application plug-in interface is not yet implemented.
