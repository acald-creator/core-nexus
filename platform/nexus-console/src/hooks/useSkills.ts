import { fetchWithAuth } from '../api/fetchWithAuth';
import { useQuery } from '@tanstack/react-query';
import { useConfig } from '../config/ConfigContext';
import type { Skill, SkillFilters } from '../api/types/skills';
import { matchesSearch } from '../utils/filters';

export function filterSkills(skills: Skill[], filters: SkillFilters): Skill[] {
  return skills.filter((s) => {
    if (filters.search && !matchesSearch(`${s.name} ${s.description}`, filters.search)) return false;
    if (filters.tag && !s.tags.includes(filters.tag)) return false;
    if (filters.domain && s.domain !== filters.domain) return false;
    return true;
  });
}

export function groupSkillsByDomain(skills: Skill[]): Map<string, Skill[]> {
  const map = new Map<string, Skill[]>();
  for (const skill of skills) {
    const group = map.get(skill.domain) || [];
    group.push(skill);
    map.set(skill.domain, group);
  }
  return map;
}

export function useSkills(filters?: SkillFilters) {
  const config = useConfig();

  const { data: allSkills = [], isLoading } = useQuery<Skill[]>({
    queryKey: ['skills'],
    queryFn: async () => {
      const response = await fetchWithAuth(`${config.apiGatewayUrl}/api/v1/skills`);
      if (!response.ok) throw new Error(`Skills fetch failed: ${response.status}`);
      return response.json();
    },
  });

  const skills = filters ? filterSkills(allSkills, filters) : allSkills;

  return { skills, isLoading };
}

export function useSkillContent(skillId: string | null) {
  const config = useConfig();

  return useQuery<string>({
    queryKey: ['skill-content', skillId],
    queryFn: async () => {
      const response = await fetchWithAuth(`${config.apiGatewayUrl}/api/v1/skills/${skillId}/content`);
      if (!response.ok) throw new Error(`Skill content fetch failed: ${response.status}`);
      return response.text();
    },
    enabled: !!skillId,
  });
}
