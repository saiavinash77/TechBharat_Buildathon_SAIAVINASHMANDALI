# Architecture — Agentic AI Meeting Assistant

![Safety-first meeting assistant workflow](docs/architecture.svg)

## Safety rule

AI suggestions are not commitments. A GitHub issue is assigned automatically only when the transcript contains an explicit self-commitment from that owner and a reviewer approves it.

| Classification | GitHub outcome |
|---|---|
| `EXPLICIT_COMMITMENT` | Create and assign the reviewer-approved issue to the confirmed owner. |
| `NEEDS_CONFIRMATION` | Create an unassigned reviewer-approved issue with `needs-confirmation`. |
| `DISCUSSION_ONLY` | Store as meeting context; block GitHub dispatch. |

See the [README](README.md) for setup and scope.
