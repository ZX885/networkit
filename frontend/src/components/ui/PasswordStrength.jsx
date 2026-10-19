import { getPasswordStrength } from '../../lib/passwordStrength.js';
import { texts } from '../../texts/en.js';
import styles from './PasswordStrength.module.css';

const t = texts.passwordStrength;
const SEGMENTS = [1, 2, 3];

// Индикатор силы пароля: полоса из 3 сегментов + текстовая метка (Weak / Medium / Strong) и подсказка,
// чего не хватает. Уровень передаётся не только цветом: есть слово и число закрашенных сегментов.
// Не привязан к форме (нужен только value), поэтому годится для регистрации, смены и сброса пароля.
// Область aria-live есть всегда (даже при пустом пароле): скринридер зачитывает смену уровня и подсказки.
// id — чтобы связать с полем через aria-describedby.
export default function PasswordStrength({ value, id }) {
  const { level, filled, hint } = getPasswordStrength(value);
  const visible = level !== 'empty';

  return (
    <div id={id} className={styles.root} data-level={level} aria-live="polite">
      {visible && (
        <>
          <div className={styles.bar} aria-hidden="true">
            {SEGMENTS.map((segment) => (
              <span key={segment} className={segment <= filled ? styles.on : styles.off} />
            ))}
          </div>
          <p className={styles.text}>
            <span className={styles.label}>
              {t.prefix} {t.levels[level]}
            </span>
            {hint && <span className={styles.hint}> — {t.hints[hint]}</span>}
          </p>
        </>
      )}
    </div>
  );
}
