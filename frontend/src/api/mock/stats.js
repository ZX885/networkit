import { sleep } from './delay.js';

// MOCK: статистика лендинга. Настоящий endpoint — GET /api/stats/ (docs/SPEC.md §3.1).
export async function getStats() {
  await sleep(700);
  return { members: 120, fields: 14, countries: 6 };
}
