import Spinner from '../ui/Spinner.jsx';
import { texts } from '../../texts/en.js';
import styles from './PageLoader.module.css';

// Экран ожидания на время проверки сессии: страницы не мигают между «гость» и «вошёл».
export default function PageLoader() {
  return (
    <div className={styles.wrap}>
      <Spinner size="lg" tone="primary" label={texts.common.loading} />
    </div>
  );
}
