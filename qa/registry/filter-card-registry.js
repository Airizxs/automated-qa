// Registry of dashboard cards that participate in filter-value QA.
// type: 'responds' → value must change when filters change.
// type: 'unfiltered-labeled' → value must stay the same, label must update.

export const FILTER_CARDS = [
  {
    id: 'sessions',
    name: 'Sessions',
    cardTestId: 'card-sessions',
    valueTestId: 'kpi-sessions',
    labelTestId: 'label-sessions',
    type: 'responds',
  },
  {
    id: 'conversion',
    name: 'Conversion Rate',
    cardTestId: 'card-conversion',
    valueTestId: 'kpi-conversion',
    labelTestId: 'label-conversion',
    type: 'responds',
  },
  {
    id: 'device-mobile',
    name: 'Device Mix — Mobile',
    cardTestId: 'card-device-mix',
    valueTestId: 'kpi-device-mobile',
    labelTestId: 'label-device-mobile',
    type: 'responds',
  },
  {
    id: 'avg-duration',
    name: 'Avg Session Duration',
    cardTestId: 'card-avg-duration',
    valueTestId: 'kpi-avg-duration',
    labelTestId: 'label-avg-duration',
    type: 'responds',
  },
  {
    id: 'total-users',
    name: 'Total Users',
    cardTestId: 'card-total-users',
    valueTestId: 'kpi-total-users',
    labelTestId: 'label-total-users',
    type: 'unfiltered-labeled',
  },
  {
    id: 'revenue-goal',
    name: 'Revenue Goal',
    cardTestId: 'card-revenue-goal',
    valueTestId: 'kpi-revenue-goal',
    labelTestId: 'label-revenue-goal',
    type: 'unfiltered-labeled',
  },
];

export const CHANNEL_OPTIONS = ['all', 'organic', 'paid', 'social', 'direct'];
export const DATE_OPTIONS = ['7', '30', '90'];

// Sections used by the smoke / visual sweep test.
export const SECTIONS = [
  { id: 'dashboard', name: 'Dashboard Demo', path: '/dashboard-demo.html' },
  { id: 'test-images', name: 'Broken Images Test', path: '/test-images.html' },
  { id: 'test-buttons', name: 'Button Test', path: '/test-buttons.html' },
];
