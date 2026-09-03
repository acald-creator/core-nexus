package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

// DumpSummary is the headless TUI snapshot for air-gapped / SSH operators (Day 19).
type DumpSummary struct {
	AgentEvents       int            `json:"agent_events"`
	Phases            map[string]int `json:"phases"`
	Alerts            int            `json:"alerts"`
	Approvals         int            `json:"approvals"`
	ApprovalsPending  int            `json:"approvals_pending"`
	Skills            int            `json:"skills"`
	AgentLog          string         `json:"agent_log"`
	AlertsFile        string         `json:"alerts_file"`
	ApprovalFile      string         `json:"approval_file"`
	SkillsDir         string         `json:"skills_dir"`
}

func dumpSummary(cfg Config) (DumpSummary, error) {
	out := DumpSummary{
		Phases:       map[string]int{},
		AgentLog:     cfg.AgentLogFile,
		AlertsFile:   cfg.AlertsFile,
		ApprovalFile: cfg.ApprovalFile,
		SkillsDir:    cfg.SkillsDir,
	}

	if cfg.AgentLogFile != "" {
		data, err := os.ReadFile(cfg.AgentLogFile)
		if err != nil && !os.IsNotExist(err) {
			return out, fmt.Errorf("agent log: %w", err)
		}
		if err == nil {
			events, _ := parseAgentLog(string(data))
			out.AgentEvents = len(events)
			for _, ev := range events {
				phase := ev.Phase
				if phase == "" {
					phase = "unknown"
				}
				out.Phases[phase]++
			}
		}
	}

	if cfg.AlertsFile != "" {
		data, err := os.ReadFile(cfg.AlertsFile)
		if err != nil && !os.IsNotExist(err) {
			return out, fmt.Errorf("alerts: %w", err)
		}
		if err == nil {
			out.Alerts = len(parseAlertsBytes(data))
		}
	}

	if cfg.ApprovalFile != "" {
		data, err := os.ReadFile(cfg.ApprovalFile)
		if err != nil && !os.IsNotExist(err) {
			return out, fmt.Errorf("approvals: %w", err)
		}
		if err == nil {
			reqs := parseApprovalsBytes(data)
			out.Approvals = len(reqs)
			for _, r := range reqs {
				if r.Status == "pending" || r.Status == "" {
					out.ApprovalsPending++
				}
			}
		}
	}

	if cfg.SkillsDir != "" {
		entries, err := os.ReadDir(cfg.SkillsDir)
		if err != nil && !os.IsNotExist(err) {
			return out, fmt.Errorf("skills: %w", err)
		}
		if err == nil {
			for _, entry := range entries {
				if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".md") {
					continue
				}
				out.Skills++
			}
		}
	}

	return out, nil
}

func parseAlertsBytes(data []byte) []Alert {
	var alerts []Alert
	if err := json.Unmarshal(data, &alerts); err == nil {
		return alerts
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		var a Alert
		if err := json.Unmarshal([]byte(line), &a); err == nil {
			alerts = append(alerts, a)
		}
	}
	return alerts
}

func parseApprovalsBytes(data []byte) []ApprovalRequest {
	var requests []ApprovalRequest
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		var r ApprovalRequest
		if err := json.Unmarshal([]byte(line), &r); err == nil {
			requests = append(requests, r)
		}
	}
	return requests
}

func writeDump(cfg Config) error {
	summary, err := dumpSummary(cfg)
	if err != nil {
		return err
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(summary)
}
