CREATE TABLE IF NOT EXISTS memory_governance (
  chunk_id TEXT PRIMARY KEY,
  memory_id TEXT,
  file_path TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  workspace TEXT NOT NULL,
  domain TEXT NOT NULL,
  privacy_level TEXT NOT NULL,
  source_trust TEXT NOT NULL,
  purpose_allow TEXT NOT NULL,
  lifecycle TEXT NOT NULL,
  sync_policy TEXT NOT NULL,
  index_policy TEXT NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memory_governance_agent ON memory_governance(agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_governance_workspace ON memory_governance(workspace);
CREATE INDEX IF NOT EXISTS idx_memory_governance_domain ON memory_governance(domain);
CREATE INDEX IF NOT EXISTS idx_memory_governance_privacy ON memory_governance(privacy_level);
