import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSkillContent } from '../../../hooks/useSkills';
import { Spinner } from '../../common/Spinner';
import styles from './Skills.module.css';

interface SkillPreviewProps {
  skillId: string;
}

export function SkillPreview({ skillId }: SkillPreviewProps) {
  const { data: content, isLoading, error } = useSkillContent(skillId);

  if (isLoading) return <Spinner />;
  if (error) return <p className={styles.error}>Failed to load skill content</p>;
  if (!content) return null;

  return (
    <div className={styles.preview}>
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </div>
  );
}
