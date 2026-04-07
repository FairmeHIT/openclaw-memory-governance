---
name: memory-classify
description: Classify OpenClaw memory files or chunks into privacy level, domain, lifecycle, and retrieval policy. Use when preparing memory governance metadata, converting raw session files into safer retrieval objects, or labeling memory before indexing, retrieval, sharing, or sync.
---

# Memory Classify

Use this skill when OpenClaw memory needs governance labels before retrieval or sharing.

## Workflow

1. Read the memory source.
2. Split raw session files into smaller chunks when possible.
3. Keep two fields:
   `raw_text`
   `retrieval_text`
4. Label each chunk with:
   `privacy_level`
   `domain`
   `purpose_allow`
   `lifecycle`
   `sync_policy`
   `index_policy`
5. Save labels outside the original OpenClaw memory files.

## Rules

- Prefer chunk-level labeling over whole-file labeling.
- Keep explicit identifiers in `raw_text`, but strip or normalize them in `retrieval_text`.
- Treat `sender_id`, `message_id`, session identifiers, and stable external IDs as high sensitivity.
- Map workspace to domain by default:
  `workspace-assistant` and `workspace-zhixi` -> `personal`
  `workspace-main` and `workspace-code` -> `work`
  `workspace-content` -> `third_party`
- Use `shared` only for memory intentionally meant to cross domains.

## Default Labels

- `L0`
  General descriptions, non-sensitive lists, low-risk behavior descriptions
- `L1`
  Agent self-introduction, routine preferences, normal task-continuity context
- `L2`
  Model/runtime details, semi-sensitive operational context, location-like context, output that should be searchable but summary-first
- `L3`
  Raw identifiers, finance, health, secrets, cross-scene identity joins, content that should not enter ordinary vector recall

## Output

Produce records with at least:

- `chunk_id`
- `memory_id`
- `agent_id`
- `workspace`
- `domain`
- `raw_text`
- `retrieval_text`
- `privacy_level`
- `purpose_allow`
- `lifecycle`
- `sync_policy`
- `index_policy`

## Reference

Read [classification.md](./references/classification.md) for the minimal label set and field meanings.
