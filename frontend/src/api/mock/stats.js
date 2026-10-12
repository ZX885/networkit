import { sleep } from './delay.js';

// MOCK: статистика лендинга. Настоящий endpoint GET /api/stats/ в backend ещё не реализован
// (docs/SPEC.md §3.1), поэтому пока возвращаем выдуманные числа.
export async function getStats() {
  await sleep(700);
  return { members: 120, fields: 14, countries: 6 };
}
