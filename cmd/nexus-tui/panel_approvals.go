package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// ApprovalRequest represents a needs_review action from the OPAR agent.
type ApprovalRequest struct {
	ID         string `json:"id"`
	Timestamp  string `json:"timestamp"`
	ScenarioID string `json:"scenario_id"`
	RunID      string `json:"run_id"`
	Target     string `json:"target"`
	Tool       string `json:"tool"`
	Action     string `json:"action"`      // what the agent wants to do
	Reason     string `json:"reason"`      // why it needs review
	Status     string `json:"status"`      // pending, approved, rejected
	Risk       string `json:"risk"`        // high, medium, low
}

// ApprovalsModel manages the approval queue panel.
type ApprovalsModel struct {
	viewport     viewport.Model
	requests     []ApprovalRequest
	approvalFile string
	cursor       int
	width        int
	height       int
	ready        bool
}

// NewApprovalsModel creates a new approvals panel.
func NewApprovalsModel(approvalFile string) ApprovalsModel {
	return ApprovalsModel{
		approvalFile: approvalFile,
		requests:     []ApprovalRequest{},
	}
}

func (m ApprovalsModel) Init() tea.Cmd {
	if m.approvalFile != "" {
		return loadApprovals(m.approvalFile)
	}
	return nil
}

func (m ApprovalsModel) PendingCount() int {
	count := 0
	for _, r := range m.requests {
		if r.Status == "pending" || r.Status == "" {
			count++
		}
	}
	return count
}

type approvalsLoaded struct {
	requests []ApprovalRequest
	err      error
}

func loadApprovals(path string) tea.Cmd {
	return func() tea.Msg {
		data, err := os.ReadFile(path)
		if err != nil {
			return approvalsLoaded{err: err}
		}

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
		return approvalsLoaded{requests: requests}
	}
}

func (m ApprovalsModel) Update(msg tea.Msg) (ApprovalsModel, tea.Cmd) {
	switch msg := msg.(type) {
	case approvalsLoaded:
		if msg.err == nil {
			m.requests = msg.requests
			m.viewport.SetContent(m.renderRequests())
		}
	case tea.KeyMsg:
		switch msg.String() {
		case "r":
			if m.approvalFile != "" {
				return m, loadApprovals(m.approvalFile)
			}
		case "j", "down":
			if m.cursor < len(m.requests)-1 {
				m.cursor++
				m.viewport.SetContent(m.renderRequests())
			}
		case "k", "up":
			if m.cursor > 0 {
				m.cursor--
				m.viewport.SetContent(m.renderRequests())
			}
		case "a":
			// Approve current item
			if m.cursor < len(m.requests) {
				m.requests[m.cursor].Status = "approved"
				m.viewport.SetContent(m.renderRequests())
			}
		case "x":
			// Reject current item
			if m.cursor < len(m.requests) {
				m.requests[m.cursor].Status = "rejected"
				m.viewport.SetContent(m.renderRequests())
			}
		}
	}

	var cmd tea.Cmd
	m.viewport, cmd = m.viewport.Update(msg)
	return m, cmd
}

func (m ApprovalsModel) View() string {
	if !m.ready {
		return panelStyle.Render("Approvals: loading...")
	}

	if len(m.requests) == 0 {
		help := subtitleStyle.Render("No approval requests.\n\n") +
			"Set NEXUS_APPROVAL_QUEUE to a JSONL file with approval request objects.\n\n" +
			"Expected format:\n" +
			`  {"id":"...","target":"...","tool":"modbus-write","action":"write reg 100=500","reason":"boundary check","status":"pending","risk":"high"}` + "\n\n" +
			subtitleStyle.Render("Keys: j/k navigate, a approve, x reject, r reload")
		return panelStyle.Render(help)
	}

	return m.viewport.View()
}

func (m ApprovalsModel) SetSize(width, height int) ApprovalsModel {
	m.width = width
	m.height = height
	if !m.ready {
		m.viewport = viewport.New(width-4, height-2)
		m.ready = true
	} else {
		m.viewport.Width = width - 4
		m.viewport.Height = height - 2
	}
	if len(m.requests) > 0 {
		m.viewport.SetContent(m.renderRequests())
	}
	return m
}

func (m ApprovalsModel) renderRequests() string {
	var b strings.Builder

	pending := m.PendingCount()
	header := fmt.Sprintf("Approval Queue — %d pending\n", pending)
	b.WriteString(titleStyle.Render(header))
	b.WriteString(strings.Repeat("─", m.width-6) + "\n\n")

	for i, r := range m.requests {
		ts := r.Timestamp
		if t, err := time.Parse(time.RFC3339, ts); err == nil {
			ts = t.Format("15:04:05")
		}

		cursor := "  "
		if i == m.cursor {
			cursor = "▶ "
		}

		statusIcon := renderApprovalStatus(r.Status)
		risk := severityStyle(r.Risk).Render(r.Risk)

		b.WriteString(fmt.Sprintf("%s%s %s [%s] %s → %s\n",
			cursor, statusIcon, subtitleStyle.Render(ts), risk, r.Target, r.Tool))
		b.WriteString(fmt.Sprintf("     Action: %s\n", r.Action))
		b.WriteString(fmt.Sprintf("     Reason: %s\n\n", subtitleStyle.Render(r.Reason)))
	}

	b.WriteString("\n" + subtitleStyle.Render("  a=approve  x=reject  r=reload"))

	return b.String()
}

func renderApprovalStatus(status string) string {
	switch status {
	case "approved":
		return lipgloss.NewStyle().Foreground(colorApproved).Render("✓")
	case "rejected":
		return lipgloss.NewStyle().Foreground(colorRejected).Render("✗")
	default:
		return lipgloss.NewStyle().Foreground(colorPending).Render("●")
	}
}
