package main

import (
	"log"
	"strings"

	"github.com/charmbracelet/bubbles/textarea"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Define styles
var (
	primaryColor   = lipgloss.Color("#04B575")
	secondaryColor = lipgloss.Color("#3C3C3C")
	textColor      = lipgloss.Color("#E2E1ED")

	headerStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFF")).
			Background(primaryColor).
			Padding(0, 1).
			Bold(true)

	sidebarStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder(), false, true, false, false).
			BorderForeground(secondaryColor).
			Padding(1, 2).
			Width(25)

	chatStyle = lipgloss.NewStyle().
			Padding(1, 2)

	inputStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder(), true, false, false, false).
			BorderForeground(secondaryColor).
			Padding(1, 2)

	agentNameStyle = lipgloss.NewStyle().Foreground(primaryColor).Bold(true)
	userNameStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("#00BFFF")).Bold(true)
)

type model struct {
	viewport       viewport.Model
	textarea       textarea.Model
	messages       []string
	sidebar        []string
	ready          bool
	terminalWidth  int
	terminalHeight int
}

func initialModel() model {
	ta := textarea.New()
	ta.Placeholder = "Type a command or message..."
	ta.Focus()
	ta.Prompt = "❯ "
	ta.CharLimit = 500
	ta.SetHeight(3)
	ta.FocusedStyle.CursorLine = lipgloss.NewStyle()
	ta.ShowLineNumbers = false

	return model{
		textarea: ta,
		messages: []string{
			agentNameStyle.Render("Nexus System") + ": System initialized. Connected to local inference engine.",
			agentNameStyle.Render("Nexus System") + ": SOC agents are ready.",
		},
		sidebar: []string{
			"AGENTS",
			" > SOC AI",
			"   Web MCP",
			"   Vault",
			"",
			"MEMORY",
			"   Events",
		},
	}
}

func (m model) Init() tea.Cmd {
	return textarea.Blink
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var (
		tiCmd tea.Cmd
		vpCmd tea.Cmd
	)

	m.textarea, tiCmd = m.textarea.Update(msg)

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.Type {
		case tea.KeyCtrlC, tea.KeyEsc:
			return m, tea.Quit
		case tea.KeyEnter:
			if msg.Alt {
				// Insert newline on Alt+Enter
				return m, tiCmd
			}
			v := m.textarea.Value()
			if strings.TrimSpace(v) != "" {
				m.messages = append(m.messages, userNameStyle.Render("You")+": "+v)
				m.messages = append(m.messages, agentNameStyle.Render("SOC AI")+": Processing request...")
				m.viewport.SetContent(strings.Join(m.messages, "\n\n"))
				m.textarea.Reset()
				m.viewport.GotoBottom()
			}
		}

	case tea.WindowSizeMsg:
		m.terminalWidth = msg.Width
		m.terminalHeight = msg.Height
		headerStyle = headerStyle.Width(msg.Width)

		sidebarWidth := sidebarStyle.GetWidth()
		mainWidth := msg.Width - sidebarWidth - 4 // Account for padding/borders

		if !m.ready {
			m.viewport = viewport.New(mainWidth, msg.Height-m.textarea.Height()-4)
			m.viewport.SetContent(strings.Join(m.messages, "\n\n"))
			m.ready = true
		} else {
			m.viewport.Width = mainWidth
			m.viewport.Height = msg.Height - m.textarea.Height() - 4
		}
		m.textarea.SetWidth(mainWidth)
	}

	m.viewport, vpCmd = m.viewport.Update(msg)

	return m, tea.Batch(tiCmd, vpCmd)
}

func (m model) View() string {
	if !m.ready {
		return "\n  Initializing..."
	}

	header := headerStyle.Render("⚡ Nexus Triage   |   Model: vLLM-Llama3   |   RAM: 4.2GB")

	sidebarContent := strings.Join(m.sidebar, "\n")
	sidebar := sidebarStyle.Height(m.terminalHeight - 2).Render(sidebarContent)

	chat := chatStyle.Render(m.viewport.View())
	input := inputStyle.Render(m.textarea.View())

	rightPane := lipgloss.JoinVertical(lipgloss.Left, chat, input)

	mainView := lipgloss.JoinHorizontal(lipgloss.Top, sidebar, rightPane)

	return lipgloss.JoinVertical(lipgloss.Left, header, mainView)
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		log.Fatal(err)
	}
}
