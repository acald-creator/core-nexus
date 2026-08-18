export interface PanelConfig {
  id: string;
  column: number;
  row: number;
  colSpan: number;
  rowSpan: number;
  visible: boolean;
}

export interface PanelArrangement {
  panels: PanelConfig[];
}

export const DEFAULT_ARRANGEMENT: PanelArrangement = {
  panels: [
    { id: 'navigation', column: 0, row: 0, colSpan: 2, rowSpan: 1, visible: true },
    { id: 'health', column: 0, row: 1, colSpan: 2, rowSpan: 1, visible: true },
  ],
};
