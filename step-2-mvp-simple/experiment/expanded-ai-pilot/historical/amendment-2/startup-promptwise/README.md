# Direct-reader startup package

**Execution amendment 2, authorized 21 October 2026.** The current coordinating chat dispatches readers directly. The Operator instructed removal of the CMD layer, push and merge, then execution in batches at maximum parallel capacity. This supersedes both earlier CMD allocations and the one-whole-trial-at-a-time restriction. The [scientific design](../PLAN.md) remains **2 models × 7 prompts × 3 efforts × 2 repeats = 84 trials, 252 independent readers and 504 paired stage records**.

Admit trials in the preserved P0–P6 order of [EXECUTION_SCHEDULE.json](EXECUTION_SCHEDULE.json), retaining original order within each prompt. Batch size follows observed native-chat/provider capacity and available RAM; overlap trials and prompt groups as capacity permits. There is no completion barrier between trials, prompts or repeat blocks. Refill capacity as readers finish; reduce new admissions if memory pressure, swapping, host responsiveness or provider limits show that concurrency is unsustainable. Use the maximum sustainable observed capacity, without artificial time/token/usage caps or an arbitrary fixed reader limit. Local RAM is an operating constraint, not a measure of remote model capacity.

| Package file | Use |
|---|---|
| [Execution schedule](EXECUTION_SCHEDULE.json) | Ordered admission of all 84 trials, with unchanged scientific identities and historical ordering provenance. |
| [Direct dispatch](DIRECT_DISPATCH.md) | Current chat's reader creation, continuation, seals, dispositions and reporting procedure. |
| [Stage A wrapper](READER_STAGE_A_WRAPPER.md) | Fresh reader's descriptor-only input and literal-output boundary. |
| [Stage B wrapper](READER_STAGE_B_WRAPPER.md) | Same-reader complete source review and page-record preservation. |
| [Transport policy](TRANSPORT_POLICY.md) | Exact bounded display, truncation recovery and observable-compaction reload. |
| [Bindings](BINDINGS.json) | Scientific input, original frozen schedule and current administrative package hashes. |

Each trial still has three independent A/B/C readers with the same assigned model, effort and Stage A template. Each reader keeps its same chat through Stage A and all 18 Stage B pages. **For that trial, all three initial attempts must be sealed or explicitly missing before any Stage B release; all three reviewed dispositions must be sealed or explicitly missing before comparison.** Parallel execution does not relax these per-trial barriers, evidence isolation or exclusive output ownership.

Retain the already-created first P0 trio and its exact inputs, chats and completed work. Do not restart it to make this amendment appear prospective. The previous coordinators relinquish dispatch; only this current chat owns the global queue and runtime roster. Historical coordinators and support/preflight sessions remain recorded but carry no active dispatch assignments. Empty reader slots are scheduled, not attempted readers.

Use the existing private runtime and tested packet/import/export/analysis helpers. The seven Stage A prompts, review prompt, addendum, catalogue, schemas and 1,062 passages remain unchanged. Relevant native preflight evidence and ten adapted-tool tests are retained, including preservation of all 654 scientific packet files and both schemas. The final independent revision-9 data-freeze review was closed on the Operator's instruction to stop further preparation; this is **not a final QA PASS**. Perform normal execution checks and report final evidence/calculation limitations; do not start another readiness campaign.

The original frozen schedule remains the private runtime's assignment binding. [SCHEDULE.json](../SCHEDULE.json) is now the canonical administrative amendment; the [historical original](../historical/revision-9-SCHEDULE.json) is preserved byte for byte. Bind the original scientific schedule and current execution schedule in an administrative sidecar, with actual chat IDs, admission batches, starts/ends and resource observations retained privately. Do not rewrite frozen packets or already sealed records to update owner fields. This package is not a standalone redistribution of the source corpus; private paths and source contents are supplied only at dispatch.

**Analysis limitations:** ordered prompt admission and resource-dependent overlapping batches can confound prompt/model/effort comparisons with timing, load and session environment. Original `block` values identify repeats, not simultaneous periods. Record the actual overlap and any capacity-driven delays. Preserve all comparisons, missingness and deviations; neither successful execution nor agreement establishes accuracy or construct validity. Collection has started; completion of the full study is not claimed.
