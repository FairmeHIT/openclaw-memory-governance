# Classification Reference

## Minimal Fields

- `privacy_level`: `L0` / `L1` / `L2` / `L3`
- `domain`: `personal` / `work` / `third_party` / `shared`
- `purpose_allow`: list such as `task_continuity`, `personalization`, `summary_only`, `sandbox_only`
- `lifecycle`: `short` / `mid` / `long` / `pending_delete`
- `sync_policy`: `local_only` / `summary_only` / `dp_sync`
- `index_policy`: `full_index` / `restricted_index` / `no_vector_recall`

## Practical Heuristics

- If a whole session file mixes identity metadata with normal dialog, split it first.
- If retrieval only needs semantic meaning, remove explicit IDs from `retrieval_text`.
- If a chunk contains runtime model information, default to `L2`, not `L0`.
- If a chunk contains only generic agent role description, default to `L1`.
- If a chunk is intended for cross-agent default behavior, consider `shared`.
