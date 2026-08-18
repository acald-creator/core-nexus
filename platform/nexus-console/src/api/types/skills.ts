export type SkillDomain = 'red-team' | 'blue-team' | 'infrastructure' | 'general';

export interface Skill {
  id: string;
  name: string;
  description: string;
  tags: string[];
  domain: SkillDomain;
  contentUrl: string;
}

export interface SkillFilters {
  search?: string;
  tag?: string;
  domain?: SkillDomain;
}
