# Session Logs (Episodic Memory)

Session logs capture what happened in each agent session — the episodic counterpart
to skills (which capture how to solve a class of problems).

## Purpose

- Track what was accomplished, by which agent, and how many tokens it cost
- Enable "what did I do last time with this target/tool?" queries
- Feed into vector memory for semantic similarity retrieval
- Audit trail for autonomous agent actions

## Schema

Each session log is a single JSONL line appended to a dated file:

```
sessions/2026-08.jsonl
sessions/2026-09.jsonl
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | yes | Unique session identifier |
| `timestamp` | string (RFC3339) | yes | When the session completed |
| `agent` | string | yes | Which agent/tool (`kiro`, `claude-code`, `codex`, `athena-opar`, `hermes`) |
| `domain` | string | yes | Skill domain (`red-team`, `blue-team`, `ics-ot`, `architecture`, etc.) |
| `repos` | string[] | no | Repositories touched |
| `task` | string | yes | One-line description of what was attempted |
| `approach` | string | yes | Brief summary of the method used |
| `outcome` | string | yes | `success`, `partial`, `failed`, `blocked` |
| `skill_generated` | string | no | Filename of skill generated (if any) |
| `skill_updated` | string | no | Filename of skill updated (if any) |
| `files_modified` | string[] | no | Key files that were changed |
| `tokens_spent` | number | no | Approximate token usage |
| `notes` | string | no | Anything else worth remembering |

### Example

```json
{"session_id":"ses-2026-08-17-001","timestamp":"2026-08-17T15:30:00Z","agent":"kiro","domain":"architecture","repos":["core-nexus","nexus-athena"],"task":"Expand architecture docs for LLM agent stimulation and emulation workflows","approach":"Context-gathered existing docs, identified gaps, updated 11-ai-native, 08-athena-fuzzer, 00-ai-collab, nexus-athena architecture.md","outcome":"success","skill_generated":"architecture-cross-repo-doc-update.md","files_modified":["docs/architecture/11-ai-native-integration-principles.md","docs/architecture/08-athena-adversary-fuzzer.md","docs/00-ai-collaboration.md"],"tokens_spent":45000,"notes":"Used cross-repo doc update pattern: deepest doc first, propagate outward"}
```

## Sync

Session logs sync to MinIO alongside skills:

```bash
# Push session logs to MinIO
mc cp docs/skills/sessions/*.jsonl nexus/nexus-memory/sessions/

# Pull from MinIO (e.g., after headless agent runs)
mc cp --recursive nexus/nexus-memory/sessions/ docs/skills/sessions/
```

## Querying (Future)

When vector memory is active, session logs are embedded and queryable:

```
"What did I do last time I worked on Modbus safe-range validation?"
→ Retrieves session ses-2026-08-15-003 with approach and outcome
→ Loads associated skill ics-ot-protocol-analysis.md into context
```
