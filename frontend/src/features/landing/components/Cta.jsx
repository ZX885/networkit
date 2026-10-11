import { useNavigate } from 'react-router-dom';
import Button from '../../../components/ui/Button.jsx';
import { texts } from '../../../texts/en.js';
import styles from './Cta.module.css';

const t = texts.landing.cta;

// Синий призыв к регистрации перед футером (legacy .cta-sec).
export default function Cta() {
  const navigate = useNavigate();

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>{t.title}</h2>
      <p className={styles.text}>{t.text}</p>
      <Button variant="inverse" size="lg" onClick={() => navigate('/register')}>
        {t.button}
      </Button>
    </section>
  );
}
