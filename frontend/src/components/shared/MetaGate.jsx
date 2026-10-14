import { Fragment } from 'react';
import useMeta from '../../api/useMeta.js';
import { apiErrorText } from '../../lib/apiErrors.js';
import { texts } from '../../texts/en.js';
import Button from '../ui/Button.jsx';
import EmptyState from '../ui/EmptyState.jsx';
import Spinner from '../ui/Spinner.jsx';
import styles from './MetaGate.module.css';

// Показывает содержимое, когда справочники сервера загружены: пока грузятся — индикатор,
// при ошибке — понятное сообщение и «Try again». Внутри шлюза useMeta() сразу отдаёт данные из кэша,
// поэтому форма не появляется наполовину пустой, а введённые данные не теряются при повторе.
// wrapper — необязательная обёртка для состояний загрузки и ошибки (например, рамка страницы).
export default function MetaGate({ children, wrapper: Wrapper = Fragment }) {
  const { status, error, retry } = useMeta();

  if (status === 'ready') return children;

  if (status === 'error') {
    return (
      <Wrapper>
        <div role="alert">
          <EmptyState
            title={texts.app.metaErrorTitle}
            description={error ? apiErrorText(error) : texts.app.errorTitle}
            action={<Button onClick={retry}>{texts.app.retry}</Button>}
          />
        </div>
      </Wrapper>
    );
  }

  return (
    <Wrapper>
      <div className={styles.center} role="status">
        <Spinner size="lg" tone="primary" label={texts.app.loading} />
      </div>
    </Wrapper>
  );
}
