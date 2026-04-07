---
name: memory-sandbox-share
description: Handle high-sensitivity OpenClaw memory through sandboxed or summary-only sharing. Use when a request touches L3 memory, external consumers ask for sensitive context, or policy requires analysis without exposing raw memory text.
---

# Memory Sandbox Share

Use this skill when memory cannot be returned directly but still needs limited use.

## When To Use

- `L3` chunks marked `sandbox_only`
- external sharing requests touching `L2` or `L3`
- requests that need aggregate results, not raw text

## Output Modes

- summary only
- label/tag extraction
- statistics only
- deny

Do not return raw text for `sandbox_only` memory.

## Workflow

1. Receive blocked or high-sensitivity chunk IDs.
2. Verify purpose and domain.
3. Prepare the smallest possible input set.
4. Run controlled analysis.
5. Return only safe output.
6. Log the job and result mode.

## Safe Defaults

- If policy is unclear, deny.
- If output could recreate raw memory, deny or coarsen it.
- Prefer a short factual summary over a full paraphrase.

## Reference

Read [sharing-modes.md](./references/sharing-modes.md) for the minimal sharing matrix.
