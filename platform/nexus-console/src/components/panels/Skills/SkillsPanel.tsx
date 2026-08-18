import { useState } from 'react';
import { useSkills } from '../../../hooks/useSkills';
import { SkillList } from './SkillList';
import { SkillPreview } from './SkillPreview';
import { Spinner } from '../../common/Spinner';
import type { SkillDomain, SkillFilters } from '../../../api/types/skills';
import styles from './Skills.module.css';

export function SkillsPanel() {
  const [filters, setFilters] = useState<SkillFilters>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { skills, isLoading } = useSkills(filters);

  return (
    <div className={styles.panel}>
      <h2>Skills Library</h2>

      <div className={styles.controls}>
        <input
          type="text"
          placeholder="Search skills..."
          value={filters.search || ''}
          onChange={(e) => setFilters({ ...filters, search: e.target.value || undefined })}
          className={styles.searchInput}
          aria-label="Search skills"
        />
        <select
          value={filters.domain || ''}
          onChange={(e) => setFilters({ ...filters, domain: (e.target.value || undefined) as SkillDomain | undefined })}
          aria-label="Filter by domain"
        >
          <option value="">All domains</option>
          <option value="red-team">Red Team</option>
          <option value="blue-team">Blue Team</option>
          <option value="infrastructure">Infrastructure</option>
          <option value="general">General</option>
        </select>
      </div>

      {isLoading ? (
        <Spinner size="lg" />
      ) : (
        <div className={styles.splitView}>
          <div className={styles.listPane}>
            {skills.length === 0 ? (
              <p className={styles.empty}>No matching skills</p>
            ) : (
              <SkillList skills={skills} selectedId={selectedId} onSelect={setSelectedId} />
            )}
          </div>
          <div className={styles.previewPane}>
            {selectedId ? (
              <SkillPreview skillId={selectedId} />
            ) : (
              <p className={styles.placeholder}>Select a skill to view its content</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
