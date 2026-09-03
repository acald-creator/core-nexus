package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDumpSummaryTestdata(t *testing.T) {
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	cfg := Config{
		AgentLogFile: filepath.Join(wd, "testdata", "agent-log.jsonl"),
		AlertsFile:   filepath.Join(wd, "testdata", "alerts.jsonl"),
		ApprovalFile: filepath.Join(wd, "testdata", "approvals.jsonl"),
		SkillsDir:    wd,
	}
	got, err := dumpSummary(cfg)
	if err != nil {
		t.Fatalf("dumpSummary: %v", err)
	}
	if got.AgentEvents != 12 {
		t.Fatalf("agent_events=%d want 12", got.AgentEvents)
	}
	if got.Phases["act"] != 3 {
		t.Fatalf("act=%d want 3", got.Phases["act"])
	}
	if got.Alerts < 1 {
		t.Fatalf("alerts=%d want >=1", got.Alerts)
	}
	if got.Approvals < 1 {
		t.Fatalf("approvals=%d want >=1", got.Approvals)
	}
}
