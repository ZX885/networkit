import SectionHeader from '../../../components/shared/SectionHeader.jsx';
import { texts } from '../../../texts/en.js';
import styles from './HowItWorks.module.css';

const t = texts.landing.how;

// Секция «How it works»: четыре шага с номерами (legacy .how).
export default function HowItWorks() {
  return (
    <section className={styles.section} id="how" aria-labelledby="how-title">
      <div className={styles.inner}>
        <SectionHeader eyebrow={t.eyebrow} title={t.title} align="center" titleId="how-title" />
        <ol className={styles.steps}>
          {t.steps.map((step, index) => (
            <li key={step.title} className={styles.step}>
              <div className={styles.number} aria-hidden="true">
                {index + 1}
              </div>
              <h3 className={styles.stepTitle}>{step.title}</h3>
              <p className={styles.stepText}>{step.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
