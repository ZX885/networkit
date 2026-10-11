import { GraduationCap, Globe, Lock, MessageCircle, Search, Target } from 'lucide-react';
import SectionHeader from '../../../components/shared/SectionHeader.jsx';
import { texts } from '../../../texts/en.js';
import styles from './Features.module.css';

const t = texts.landing.features;
// Ключ иконки из texts → компонент lucide
const ICONS = {
  search: Search,
  globe: Globe,
  target: Target,
  message: MessageCircle,
  lock: Lock,
  cap: GraduationCap,
};

// Секция «Why NetworkIt»: шесть карточек возможностей (legacy .features).
export default function Features() {
  return (
    <section className={styles.section} id="features" aria-labelledby="features-title">
      <div className={styles.inner}>
        <SectionHeader
          eyebrow={t.eyebrow}
          title={t.title}
          subtitle={t.subtitle}
          titleId="features-title"
        />
        <div className={styles.grid}>
          {t.items.map((item) => {
            const Icon = ICONS[item.icon];
            return (
              <article key={item.title} className={styles.card}>
                <div className={styles.icon} aria-hidden="true">
                  <Icon size={20} />
                </div>
                <h3 className={styles.cardTitle}>{item.title}</h3>
                <p className={styles.cardText}>{item.text}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
