package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
)

// SkillEntry represents a discovered skill file.
type SkillEntry struct {
	Name     string
	Path     string
	Content  string
	Tags     string
}

// SkillsModel manages the skill browser panel.
type SkillsModel struct {
	viewport  viewport.Model
	skills    []SkillEntry
	skillsDir string
	cursor    int
	viewing   bool // true when viewing a specific skill's content
	width     int
	height    int
	ready     bool
}

// NewSkillsModel creates a new skills browser panel.
func NewSkillsModel(skillsDir string) SkillsModel {
	return SkillsModel{
		skillsDir: skillsDir,
		skills:    []SkillEntry{},
	}
}

func (m SkillsModel) Init() tea.Cmd {
	if m.skillsDir != "" {
		return loadSkills(m.skillsDir)
	}
	return nil
}

type skillsLoaded struct {
	skills []SkillEntry
	err    error
}

func loadSkills(dir string) tea.Cmd {
	return func() tea.Msg {
		entries, err := os.ReadDir(dir)
		if err != nil {
			return skillsLoaded{err: err}
		}

		var skills []SkillEntry
		for _, entry := range entries {
			if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".md") {
				continue
			}

			path := filepath.Join(dir, entry.Name())
			content, err := os.ReadFile(path)
			if err != nil {
				continue
			}

			name := strings.TrimSuffix(entry.Name(), ".md")
			tags := extractTags(string(content))

			skills = append(skills, SkillEntry{
				Name:    name,
				Path:    path,
				Content: string(content),
				Tags:    tags,
			})
		}
		return skillsLoaded{skills: skills}
	}
}

// extractTags pulls the tags line from front matter.
func extractTags(content string) string {
	lines := strings.Split(content, "\n")
	inFrontMatter := false
	for _, line := range lines {
		if strings.TrimSpace(line) == "---" {
			if inFrontMatter {
				break
			}
			inFrontMatter = true
			continue
		}
		if inFrontMatter && strings.HasPrefix(line, "tags:") {
			return strings.TrimPrefix(line, "tags:")
		}
	}
	return ""
}

func (m SkillsModel) Update(msg tea.Msg) (SkillsModel, tea.Cmd) {
	switch msg := msg.(type) {
	case skillsLoaded:
		if msg.err == nil {
			m.skills = msg.skills
			m.viewport.SetContent(m.renderList())
		}
	case tea.KeyMsg:
		if m.viewing {
			switch msg.String() {
			case "esc", "backspace":
				m.viewing = false
				m.viewport.SetContent(m.renderList())
				m.viewport.GotoTop()
				return m, nil
			}
		} else {
			switch msg.String() {
			case "r":
				if m.skillsDir != "" {
					return m, loadSkills(m.skillsDir)
				}
			case "j", "down":
				if m.cursor < len(m.skills)-1 {
					m.cursor++
					m.viewport.SetContent(m.renderList())
				}
			case "k", "up":
				if m.cursor > 0 {
					m.cursor--
					m.viewport.SetContent(m.renderList())
				}
			case "enter":
				if m.cursor < len(m.skills) {
					m.viewing = true
					m.viewport.SetContent(m.renderSkillDetail())
					m.viewport.GotoTop()
					return m, nil
				}
			}
		}
	}

	var cmd tea.Cmd
	m.viewport, cmd = m.viewport.Update(msg)
	return m, cmd
}

func (m SkillsModel) View() string {
	if !m.ready {
		return panelStyle.Render("Skills: loading...")
	}

	if len(m.skills) == 0 {
		help := subtitleStyle.Render("No skills found.\n\n") +
			fmt.Sprintf("Looking in: %s\n\n", m.skillsDir) +
			"Skills are auto-generated after sessions that solve novel problems.\n" +
			"They encode proven approaches for reuse across sessions.\n\n" +
			subtitleStyle.Render("Keys: r to reload")
		return panelStyle.Render(help)
	}

	return m.viewport.View()
}

func (m SkillsModel) SetSize(width, height int) SkillsModel {
	m.width = width
	m.height = height
	if !m.ready {
		m.viewport = viewport.New(width-4, height-2)
		m.ready = true
	} else {
		m.viewport.Width = width - 4
		m.viewport.Height = height - 2
	}
	if len(m.skills) > 0 {
		if m.viewing {
			m.viewport.SetContent(m.renderSkillDetail())
		} else {
			m.viewport.SetContent(m.renderList())
		}
	}
	return m
}

func (m SkillsModel) renderList() string {
	var b strings.Builder

	header := fmt.Sprintf("Skills Library — %d skills loaded from %s\n", len(m.skills), m.skillsDir)
	b.WriteString(titleStyle.Render(header))
	b.WriteString(strings.Repeat("─", m.width-6) + "\n\n")

	for i, s := range m.skills {
		cursor := "  "
		if i == m.cursor {
			cursor = "▶ "
		}

		name := s.Name
		tags := subtitleStyle.Render(strings.TrimSpace(s.Tags))

		b.WriteString(fmt.Sprintf("%s%s  %s\n", cursor, titleStyle.Render(name), tags))
	}

	b.WriteString("\n" + subtitleStyle.Render("  j/k navigate, enter view, r reload"))

	return b.String()
}

func (m SkillsModel) renderSkillDetail() string {
	if m.cursor >= len(m.skills) {
		return ""
	}

	skill := m.skills[m.cursor]
	var b strings.Builder

	b.WriteString(titleStyle.Render(skill.Name) + "\n")
	b.WriteString(subtitleStyle.Render(skill.Path) + "\n")
	b.WriteString(strings.Repeat("─", m.width-6) + "\n\n")
	b.WriteString(skill.Content)
	b.WriteString("\n\n" + subtitleStyle.Render("  esc/backspace to return to list"))

	return b.String()
}
