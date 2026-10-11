import { useNavigate } from 'react-router-dom';
import { Rocket } from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import { formatStat } from '../../../lib/formatStat.js';
import { texts } from '../../../texts/en.js';
import useStats from '../hooks/useStats.js';
import HeroCanvas from './HeroCanvas.jsx';
import styles from './Hero.module.css';

const t = texts.landing.hero;

// Первый экран: заголовок, кнопки и блок статистики (legacy .hero).
export default function Hero() {
  const navigate = useNavigate();
  const stats = useStats();
  const items = [
    { key: 'members', label: t.members },
    { key: 'fields', label: t.fields },
    { key: 'countries', label: t.countries },
  ];

  return (
    <section className={styles.hero}>
      <HeroCanvas />
      <p className={styles.eyebrow}>
        <Rocket size={14} aria-hidden="true" /> {t.eyebrow}
      </p>
      <h1 className={styles.title}>
        {t.titleBefore}
        <br />
        {t.titleMiddle}
        <span>{t.titleAccent}</span>
      </h1>
      <p className={styles.subtitle}>{t.subtitle}</p>
      <div className={styles.ctas}>
        <Button size="lg" onClick={() => navigate('/register')}>
          {t.primaryCta}
        </Button>
        <Button variant="ghost" size="lg" onClick={() => navigate('/login')}>
          {t.secondaryCta}
        </Button>
      </div>
      <div className={styles.stats} role="group" aria-label={t.statsLabel}>
        {items.map((item) => (
          <div key={item.key} className={styles.stat}>
            <strong>{stats ? formatStat(stats[item.key], t.statsEmpty) : '—'}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
