// Формат числа статистики на лендинге — как fmt() в legacy updateHeroStats:
// 0 → «Be first!», 1–9 → «5», 10–99 → «20+», 100 и больше → округление вниз до сотен + «+».
export function formatStat(n, emptyText) {
  if (n === 0) return emptyText;
  if (n < 10) return String(n);
  if (n < 100) return `${n}+`;
  return `${Math.floor(n / 100) * 100}+`;
}
