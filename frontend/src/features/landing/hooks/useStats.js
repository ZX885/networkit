import { useEffect, useState } from 'react';
import { getStats } from '../../../api/mock/stats.js';

// Статистика лендинга: null, пока грузится (на экране «—»), затем { members, fields, countries }.
export default function useStats() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getStats()
      .then((result) => {
        if (!cancelled) setStats(result);
      })
      .catch(() => {}); // при ошибке остаётся «—»
    return () => {
      cancelled = true;
    };
  }, []);

  return stats;
}
