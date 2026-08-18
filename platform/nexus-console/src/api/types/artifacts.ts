export type ArtifactCategory = 'pcaps' | 'sboms' | 'skills' | 'sessions';

export interface ArtifactObject {
  key: string;
  name: string;
  size: number;
  lastModified: string;
  category: ArtifactCategory;
}
