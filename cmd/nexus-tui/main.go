package main

import (
	"log"
	"os"

	tea "github.com/charmbracelet/bubbletea"
)

func main() {
	// Allow config directory override via env
	skillsDir := os.Getenv("NEXUS_SKILLS_DIR")
	if skillsDir == "" {
		home, _ := os.UserHomeDir()
		skillsDir = home + "/.kiro/skills"
	}

	alertsFile := os.Getenv("NEXUS_ALERTS_FILE")
	agentLogFile := os.Getenv("NEXUS_AGENT_LOG")
	approvalFile := os.Getenv("NEXUS_APPROVAL_QUEUE")

	cfg := Config{
		SkillsDir:    skillsDir,
		AlertsFile:   alertsFile,
		AgentLogFile: agentLogFile,
		ApprovalFile: approvalFile,
	}

	p := tea.NewProgram(NewApp(cfg), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		log.Fatal(err)
	}
}
