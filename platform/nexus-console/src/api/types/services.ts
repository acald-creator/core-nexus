import type { ServiceCategory } from '../../config/types';

export type { ServiceEntry, ServiceCategory } from '../../config/types';

export interface ServiceGroup {
  category: ServiceCategory;
  services: import('../../config/types').ServiceEntry[];
}
