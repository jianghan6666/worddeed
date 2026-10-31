# Application replication

Reproduction requirements are application-specific: data access, environments, scientific settings and acceptance checks belong to the application that produced the results.

| Application | Instructions and evidence | Verified outputs |
| --- | --- | --- |
| [CEO risk preference](applications/ceo-risk-preference/README.md) | [Complete replication guide](applications/ceo-risk-preference/REPLICATION.md) | [Verified release](https://github.com/joyzhzh/ai-microfoundation-proxy/releases/tag/reviewer-replication-2026-10-31) |

Start with the [reviewer guide](docs/REVIEWER_GUIDE.md) for a fresh ZIP or clone, lightweight checks and a step-by-step account of what is replayed and what is newly fitted.

The CEO package includes the available original data/model assets, saved reader evidence, scientific code, results and executed verification. Its guide explains the pinned environment, saved-representation boundary and fresh model-fitting/estimation checks.

[replication/](replication/README.md) holds archive utilities and the current execution drivers. Those empirical drivers currently target the CEO application. Another application needs its own scientific specification and compatible adapters; follow [Adding an application](docs/NEW_APPLICATION.md). Keep each application's manifests and verification receipts in its own `applications/<application-name>/replication/` folder.
