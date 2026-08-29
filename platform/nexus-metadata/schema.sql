-- Artifact / run provenance index (blobs live on R2; this is metadata only).
CREATE TABLE IF NOT EXISTS artifacts (
  id TEXT PRIMARY KEY,
  object_key TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  digest TEXT,
  media_type TEXT,
  size_bytes INTEGER,
  source TEXT NOT NULL DEFAULT 'gateway',
  image_ref TEXT,
  ssf_attestation_url TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at TEXT,
  actor TEXT,
  summary TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS run_artifacts (
  run_id TEXT NOT NULL,
  artifact_id TEXT NOT NULL,
  PRIMARY KEY (run_id, artifact_id),
  FOREIGN KEY (run_id) REFERENCES runs(id),
  FOREIGN KEY (artifact_id) REFERENCES artifacts(id)
);

CREATE INDEX IF NOT EXISTS idx_artifacts_category ON artifacts(category);
CREATE INDEX IF NOT EXISTS idx_artifacts_digest ON artifacts(digest);
CREATE INDEX IF NOT EXISTS idx_runs_kind ON runs(kind);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
