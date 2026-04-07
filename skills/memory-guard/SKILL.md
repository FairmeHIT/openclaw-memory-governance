---
name: memory-guard
description: Enforce policy before OpenClaw memory is returned to an agent, tool, or external consumer. Use when retrieval needs domain isolation, privacy-aware filtering, downgrade-to-summary behavior, or sandbox routing for high-sensitivity memory.
---

# Memory Guard

Use this skill to decide whether candidate memory chunks should be allowed, denied, downgraded, or sandboxed before they are returned.

## Decision Flow

1. Start with a candidate chunk set from retrieval.
2. Read governance metadata for each chunk.
3. Evaluate:
   requester workspace/domain
   purpose
   privacy level
   lifecycle
   index policy
4. Return one of:
   `allow`
   `deny`
   `downgrade`
   `sandbox`

## Default Policy

- Deny cross-domain memory unless domain is `shared`.
- Deny any `pending_delete` memory.
- For `L3`:
  use `sandbox` if policy says `sandbox_only`
  otherwise downgrade or deny
- For `L2`:
  default to `downgrade`
  only return raw text under stricter rules than normal retrieval
- For `external_share`:
  deny `L2` and `L3` raw output
  permit at most summary-only output

## Output Discipline

- `allow` means raw text may be returned.
- `downgrade` means return summary, tags, or safe explanation instead of raw text.
- `sandbox` means queue controlled processing and do not return raw text directly.
- `deny` means no content return.

## Validation

Check that policy reduces:

- cross-domain leakage
- unauthorized recall
- sensitive raw exposure

without collapsing normal task success.

## Reference

Read [policy.md](./references/policy.md) for the minimal rule matrix.
