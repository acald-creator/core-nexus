import type { ArtifactObject } from '../../../api/types/artifacts';
import { formatFileSize, formatDate } from '../../../utils/formatters';
import styles from './Artifacts.module.css';

interface ArtifactListProps {
  objects: ArtifactObject[];
  onDownload: (key: string) => void;
}

export function ArtifactList({ objects, onDownload }: ArtifactListProps) {
  return (
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Name</th>
          <th>Size</th>
          <th>Modified</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {objects.map((obj) => (
          <tr key={obj.key} className={styles.row}>
            <td className={styles.name}>{obj.name}</td>
            <td className={styles.size}>{formatFileSize(obj.size)}</td>
            <td className={styles.date}>{formatDate(obj.lastModified)}</td>
            <td>
              <button
                className={styles.downloadBtn}
                onClick={() => onDownload(obj.key)}
                aria-label={`Download ${obj.name}`}
              >
                ↓
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
