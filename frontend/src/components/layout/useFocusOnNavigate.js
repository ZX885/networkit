import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

const WATCH_MS = 1500; // столько ждём, пока страница дорисует свой заголовок после загрузки данных

function focusHeading(container) {
  const target = container.querySelector('h1') ?? container;
  target.setAttribute('tabindex', '-1');
  target.focus();
}

// При смене страницы переводим фокус на её заголовок h1 (или на сам контейнер), чтобы скринридер
// и клавиатура начинали с новой страницы. Если заголовок заменился после загрузки данных и фокус
// пропал (ушёл на body), возвращаем его на новый заголовок. Внутри /messages фокус не трогаем:
// там меняется только чат.
export default function useFocusOnNavigate(containerRef) {
  const { pathname } = useLocation();
  const key = pathname.startsWith('/messages') ? '/messages' : pathname;
  const isFirstRender = useRef(true);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return undefined;
    }
    const container = containerRef.current;
    if (!container) return undefined;
    focusHeading(container);

    const observer = new MutationObserver(() => {
      if (document.activeElement === document.body) focusHeading(container);
    });
    observer.observe(container, { childList: true, subtree: true });
    const timer = setTimeout(() => observer.disconnect(), WATCH_MS);
    return () => {
      clearTimeout(timer);
      observer.disconnect();
    };
  }, [key, containerRef]);
}
