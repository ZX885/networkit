// MOCK: имитация сетевой задержки. Нужна только мок-статистике лендинга (backend /api/stats/ ещё нет).
export function sleep(ms = 600) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
