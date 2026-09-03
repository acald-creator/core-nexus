package main

import (
	"flag"
	"log"
	"os"

	tea "github.com/charmbracelet/bubbletea"
)

func main() {
	dump := flag.Bool("dump", false, "print JSON panel counts and exit (air-gapped / SSH, no TTY)")
	flag.Parse()

	skillsDir := os.Getenv("NEXUS_SKILLS_DIR")
	if skillsDir == "" {
		home, _ := os.UserHomeDir()
		skillsDir = home + "/.kiro/skills"
	}

	cfg := Config{
		SkillsDir:    skillsDir,
		AlertsFile:   os.Getenv("NEXUS_ALERTS_FILE"),
		AgentLogFile: os.Getenv("NEXUS_AGENT_LOG"),
		ApprovalFile: os.Getenv("NEXUS_APPROVAL_QUEUE"),
	}

	if *dump {
		if err := writeDump(cfg); err != nil {
			log.Fatal(err)
		}
		return
	}

	p := tea.NewProgram(NewApp(cfg), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		log.Fatal(err)
	}
}
