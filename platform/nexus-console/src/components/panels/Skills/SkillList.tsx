import type { Skill } from '../../../api/types/skills';
import styles from './Skills.module.css';

interface SkillListProps {
  skills: Skill[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function SkillList({ skills, selectedId, onSelect }: SkillListProps) {
  return (
    <div className={styles.list}>
      {skills.map((skill) => (
        <div
          key={skill.id}
          className={`${styles.listItem} ${selectedId === skill.id ? styles.listItemActive : ''}`}
          onClick={() => onSelect(skill.id)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onSelect(skill.id)}
        >
          <span className={styles.skillName}>{skill.name}</span>
          <span className={styles.skillDesc}>{skill.description}</span>
          <div className={styles.tags}>
            {skill.tags.map((tag) => (
              <span key={tag} className={styles.tag}>{tag}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
