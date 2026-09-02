import { useState } from 'react';
import { useArtifacts } from '../../../hooks/useArtifacts';
import { ArtifactList } from './ArtifactList';
import { ErrorBanner } from '../../common/ErrorBanner';
import { Spinner } from '../../common/Spinner';
import type { ArtifactCategory } from '../../../api/types/artifacts';
import styles from './Artifacts.module.css';

const CATEGORIES: { id: ArtifactCategory; label: string }[] = [
  { id: 'pcaps', label: 'PCAPs' },
  { id: 'sboms', label: 'SBOMs' },
  { id: 'skills', label: 'Skills' },
  { id: 'sessions', label: 'Sessions' },
];

export function ArtifactsView() {
  const [category, setCategory] = useState<ArtifactCategory>('pcaps');
  const { objects, isLoading, error, getDownloadUrl } = useArtifacts(category);

  const handleDownload = async (key: string) => {
    try {
      const url = await getDownloadUrl(key);
      window.open(url, '_blank');
    } catch {
      alert('Download failed — retry via the gateway Artifacts API or check object-store credentials');
    }
  };

  return (
    <div className={styles.panel}>
      <h2>Artifacts</h2>
      <p className={styles.hint}>MinIO in lab overlays; Cloudflare R2 + D1 on production-like paths (ADR 0005).</p>

      <div className={styles.categoryTabs}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            className={`${styles.tab} ${category === cat.id ? styles.tabActive : ''}`}
            onClick={() => setCategory(cat.id)}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {error && (
        <ErrorBanner message="Object store unavailable via gateway — check MinIO/R2 credentials and NEXUS_GW_* settings" />
      )}

      {isLoading ? (
        <Spinner size="lg" />
      ) : objects.length === 0 ? (
        <p className={styles.empty}>No {category} artifacts found</p>
      ) : (
        <ArtifactList objects={objects} onDownload={handleDownload} />
      )}
    </div>
  );
}
