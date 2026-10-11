import { ChevronLeft, ChevronRight } from 'lucide-react';
import styles from './Pagination.module.css';

// Список для показа: первая, последняя и соседи текущей страницы; пропуски — 'gap-1' / 'gap-2'.
function getPageItems(page, pageCount) {
  const wanted = new Set([1, pageCount, page - 1, page, page + 1]);
  const pages = [...wanted].filter((n) => n >= 1 && n <= pageCount).sort((a, b) => a - b);
  const items = [];
  pages.forEach((n, i) => {
    if (i > 0 && n - pages[i - 1] > 1) items.push(`gap-${i}`);
    items.push(n);
  });
  return items;
}

// Пагинация. Тексты (label, prevLabel, nextLabel, pageLabel) передаёт вызывающий код.
// pageLabel — функция: (номер) => 'Page 3'.
export default function Pagination({
  page,
  pageCount,
  onChange,
  label,
  prevLabel,
  nextLabel,
  pageLabel,
}) {
  if (pageCount <= 1) return null;

  return (
    <nav className={styles.nav} aria-label={label}>
      <button
        type="button"
        className={styles.page}
        disabled={page <= 1}
        aria-label={prevLabel}
        onClick={() => onChange(page - 1)}
      >
        <ChevronLeft size={16} aria-hidden="true" />
      </button>
      {getPageItems(page, pageCount).map((item) =>
        typeof item === 'string' ? (
          <span key={item} className={styles.gap} aria-hidden="true">
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            className={[styles.page, item === page && styles.current].filter(Boolean).join(' ')}
            aria-label={pageLabel(item)}
            aria-current={item === page ? 'page' : undefined}
            onClick={() => onChange(item)}
          >
            {item}
          </button>
        ),
      )}
      <button
        type="button"
        className={styles.page}
        disabled={page >= pageCount}
        aria-label={nextLabel}
        onClick={() => onChange(page + 1)}
      >
        <ChevronRight size={16} aria-hidden="true" />
      </button>
    </nav>
  );
}
