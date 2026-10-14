import { useEffect, useState } from 'react';
import { getCachedMeta, loadMeta } from './meta.js';

// Справочники сервера: { status: 'loading' | 'ready' | 'error', meta, error, retry }.
// Данные берутся из кэша в памяти (api/meta.js), поэтому повторные вызовы мгновенные.
export default function useMeta() {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState(() => {
    const meta = getCachedMeta();
    return meta ? { attempt: 0, meta, error: null } : { attempt: null, meta: null, error: null };
  });

  useEffect(() => {
    if (getCachedMeta()) return undefined;
    let ignore = false;
    loadMeta().then(
      (meta) => !ignore && setState({ attempt, meta, error: null }),
      (error) => !ignore && setState({ attempt, meta: null, error }),
    );
    return () => {
      ignore = true;
    };
  }, [attempt]);

  const meta = state.meta ?? getCachedMeta();
  let status = 'loading';
  if (meta) status = 'ready';
  else if (state.attempt === attempt && state.error) status = 'error';

  return { status, meta, error: state.error, retry: () => setAttempt((n) => n + 1) };
}
