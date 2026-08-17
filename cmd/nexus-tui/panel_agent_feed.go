package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
)

// OPAREvent represents a single event from the agent OPAR loop.
type OPAREvent struct {
	Timestamp  string `json:"timestamp"`
	Phase      string `json:"phase"` // observe, plan, act, reflect
	ScenarioID string `json:"scenario_id"`
	RunID      string `json:"run_id"`
	Target     string `json:"target"`
	Tool       string `json:"tool,omitempty"`
	Technique  string `json:"technique,omitempty"`
	Summary    string `json:"summary"`
	Label      string `json:"label,omitempty"` // ground-truth label
}

// AgentFeedModel manages the OPAR agent feed panel.
type AgentFeedModel struct {
	viewport viewport.Model
	events   []OPAREvent
	logFile  string
	width    int
	height   int
	ready    bool
}

// NewAgentFeedModel creates a new agent feed panel.
func NewAgentFeedModel(logFile string) AgentFeedModel {
	return AgentFeedModel{
		logFile: logFile,
		events:  []OPAREvent{},
	}
}

func (m AgentFeedModel) Init() tea.Cmd {
	if m.logFile != "" {
		return loadAgentLog(m.logFile)
	}
	return nil
}

type agentLogLoaded struct {
	events []OPAREvent
	err    error
}

func loadAgentLog(path string) tea.Cmd {
	return func() tea.Msg {
		data, err := os.ReadFile(path)
		if err != nil {
			return agentLogLoaded{err: err}
		}

		var events []OPAREvent
		for _, line := range strings.Split(string(data), "\n") {
			line = strings.TrimSpace(line)
			if line == "" {
				continue
			}
			var ev OPAREvent
			if err := json.Unmarshal([]byte(line), &ev); err == nil {
				events = append(events, ev)
			}
		}
		return agentLogLoaded{events: events}
	}
}

func (m AgentFeedModel) Update(msg tea.Msg) (AgentFeedModel, tea.Cmd) {
	switch msg := msg.(type) {
	case agentLogLoaded:
		if msg.err == nil {
			m.events = msg.events
			m.viewport.SetContent(m.renderEvents())
			m.viewport.GotoBottom()
		}
	case tea.KeyMsg:
		switch msg.String() {
		case "r":
			// Reload log
			if m.logFile != "" {
				return m, loadAgentLog(m.logFile)
			}
		}
	}

	var cmd tea.Cmd
	m.viewport, cmd = m.viewport.Update(msg)
	return m, cmd
}

func (m AgentFeedModel) View() string {
	if !m.ready {
		return panelStyle.Render("Agent Feed: loading...")
	}

	if len(m.events) == 0 {
		help := subtitleStyle.Render("No agent events loaded.\n\n") +
			"Set NEXUS_AGENT_LOG to a JSONL file with OPAR events, or press 'r' to reload.\n\n" +
			"Expected format (one JSON object per line):\n" +
			`  {"timestamp":"...","phase":"observe","scenario_id":"...","summary":"..."}` + "\n\n" +
			subtitleStyle.Render("Phases: observe → plan → act → reflect")
		return panelStyle.Render(help)
	}

	return m.viewport.View()
}

func (m AgentFeedModel) SetSize(width, height int) AgentFeedModel {
	m.width = width
	m.height = height
	if !m.ready {
		m.viewport = viewport.New(width-4, height-2)
		m.ready = true
	} else {
		m.viewport.Width = width - 4
		m.viewport.Height = height - 2
	}
	if len(m.events) > 0 {
		m.viewport.SetContent(m.renderEvents())
	}
	return m
}

func (m AgentFeedModel) renderEvents() string {
	var b strings.Builder
	for _, ev := range m.events {
		ts := ev.Timestamp
		if t, err := time.Parse(time.RFC3339, ts); err == nil {
			ts = t.Format("15:04:05")
		}

		phase := renderPhase(ev.Phase)
		line := fmt.Sprintf("%s %s [%s] %s", subtitleStyle.Render(ts), phase, ev.Target, ev.Summary)

		if ev.Tool != "" {
			line += fmt.Sprintf(" tool=%s", ev.Tool)
		}
		if ev.Label != "" {
			line += fmt.Sprintf(" label=%s", ev.Label)
		}

		b.WriteString(line)
		b.WriteString("\n")
	}
	return b.String()
}

func renderPhase(phase string) string {
	switch phase {
	case "observe":
		return phaseObserveStyle.Render("OBSERVE")
	case "plan":
		return phasePlanStyle.Render("PLAN   ")
	case "act":
		return phaseActStyle.Render("ACT    ")
	case "reflect":
		return phaseReflectStyle.Render("REFLECT")
	default:
		return phase
	}
}
