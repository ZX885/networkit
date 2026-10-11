import { MessageCircle, Trash2 } from 'lucide-react';
import Button from '../../components/ui/Button.jsx';
import Section from './Section.jsx';
import layout from './Section.module.css';

const VARIANTS = ['primary', 'ghost', 'danger'];
const SIZES = ['sm', 'md', 'lg'];

// Все варианты и размеры кнопок + состояния loading и disabled
export default function ButtonsSection() {
  return (
    <Section title="Button">
      {VARIANTS.map((variant) => (
        <div key={variant}>
          <p className={layout.caption}>{variant}</p>
          <div className={layout.row}>
            {SIZES.map((size) => (
              <Button key={size} variant={variant} size={size}>
                {size} button
              </Button>
            ))}
            <Button variant={variant} loading>
              Loading
            </Button>
            <Button variant={variant} disabled>
              Disabled
            </Button>
          </div>
        </div>
      ))}
      <p className={layout.caption}>with icon / full width</p>
      <div className={layout.row}>
        <Button size="sm">
          <MessageCircle size={16} aria-hidden="true" /> Message
        </Button>
        <Button variant="danger" size="sm">
          <Trash2 size={16} aria-hidden="true" /> Delete
        </Button>
      </div>
      <div className={layout.col}>
        <Button fullWidth>Full width</Button>
      </div>
      <p className={layout.caption}>inverse (on primary background)</p>
      <div
        className={layout.row}
        style={{
          background: 'var(--primary)',
          padding: 'var(--space-4)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <Button variant="inverse" size="lg">
          Get started
        </Button>
      </div>
    </Section>
  );
}
