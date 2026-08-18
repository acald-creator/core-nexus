import { useQuery } from '@tanstack/react-query';
import { useConfig } from '../config/ConfigContext';
import type { ArtifactCategory, ArtifactObject } from '../api/types/artifacts';

export function useArtifacts(category: ArtifactCategory) {
  const config = useConfig();

  const { data: objects = [], isLoading, error } = useQuery<ArtifactObject[]>({
    queryKey: ['artifacts', category],
    queryFn: async () => {
      const response = await fetch(`${config.apiGatewayUrl}/api/v1/artifacts?category=${category}`);
      if (!response.ok) throw new Error(`Artifacts fetch failed: ${response.status}`);
      return response.json();
    },
  });

  const getDownloadUrl = async (key: string): Promise<string> => {
    const response = await fetch(`${config.apiGatewayUrl}/api/v1/artifacts/${encodeURIComponent(key)}/download-url`);
    if (!response.ok) throw new Error(`Download URL fetch failed: ${response.status}`);
    const data = await response.json();
    return data.url;
  };

  return { objects, isLoading, error, getDownloadUrl };
}
