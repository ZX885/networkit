import { texts } from '../../../../texts/en.js';
import styles from './RegisterProgress.module.css';

const t = texts.register;

// Прогресс регистрации: «Step N of 8», название шага, полоса и точки (legacy .rprog).
export default function RegisterProgress({ step, total }) {
  const name = t.stepNames[step - 1];

  return (
    <div className={styles.progress}>
      <div className={styles.label}>
        <span>{t.stepOf(step, total)}</span>
        <strong>{name}</strong>
      </div>
      <div
        className={styles.track}
        role="progressbar"
        aria-label={t.progress}
        aria-valuemin={1}
        aria-valuemax={total}
        aria-valuenow={step}
        aria-valuetext={`${t.stepOf(step, total)}: ${name}`}
      >
        <div className={styles.fill} style={{ width: `${(step / total) * 100}%` }} />
      </div>
      <div className={styles.dots} aria-hidden="true">
        {Array.from({ length: total }, (_, index) => {
          const state = index < step - 1 ? styles.done : index === step - 1 ? styles.active : '';
          return <span key={index} className={[styles.dot, state].join(' ')} />;
        })}
      </div>
    </div>
  );
}
