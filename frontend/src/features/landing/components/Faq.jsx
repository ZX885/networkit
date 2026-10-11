import { useId, useState } from 'react';
import { Plus } from 'lucide-react';
import SectionHeader from '../../../components/shared/SectionHeader.jsx';
import { texts } from '../../../texts/en.js';
import styles from './Faq.module.css';

const t = texts.landing.faq;

// FAQ-аккордеон. Вопрос — кнопка с aria-expanded; ответ раскрывается на полную высоту
// (в legacy max-height обрезал длинные ответы). Несколько ответов могут быть открыты одновременно.
export default function Faq() {
  const baseId = useId();
  const [openItems, setOpenItems] = useState(() => new Set());

  function toggle(index) {
    setOpenItems((current) => {
      const next = new Set(current);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  }

  return (
    <section className={styles.section} id="faq" aria-labelledby="faq-title">
      <div className={styles.inner}>
        <SectionHeader eyebrow={t.eyebrow} title={t.title} align="center" titleId="faq-title" />
        <div className={styles.list}>
          {t.items.map((item, index) => {
            const isOpen = openItems.has(index);
            const questionId = `${baseId}-q${index}`;
            const answerId = `${baseId}-a${index}`;
            return (
              <div
                key={item.q}
                className={[styles.item, isOpen && styles.open].filter(Boolean).join(' ')}
              >
                <h3 className={styles.heading}>
                  <button
                    type="button"
                    id={questionId}
                    className={styles.question}
                    aria-expanded={isOpen}
                    aria-controls={answerId}
                    onClick={() => toggle(index)}
                  >
                    {item.q}
                    <span className={styles.icon} aria-hidden="true">
                      <Plus size={16} />
                    </span>
                  </button>
                </h3>
                <div
                  id={answerId}
                  role="region"
                  aria-labelledby={questionId}
                  className={styles.answer}
                >
                  <div className={styles.answerInner}>
                    <p>{item.a}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
