package main

// Config holds runtime configuration for the TUI.
type Config struct {
	SkillsDir    string // Directory containing skill markdown files
	AlertsFile   string // Path to JSON alerts file (Wazuh/Suricata format)
	AgentLogFile string // Path to OPAR agent event log (JSONL)
	ApprovalFile string // Path to approval queue file (JSONL)
}
