import styles from './ChipSelect.module.css';

// Выбор из вариантов кнопками-чипами (aria-pressed).
// options: [{ code, label, icon? }]; value — массив выбранных кодов.
// multiple=false — можно выбрать только один (повторный клик не снимает выбор).
// max — максимум выбранных (остальные блокируются).
// variant: 'chip' (сетка, интересы) | 'pill' (ряд пилюль, пол и статус) | 'list' (колонка с иконками, цели).
export default function ChipSelect({
  options,
  value,
  onChange,
  multiple = true,
  max,
  variant = 'chip',
  label,
  describedBy,
}) {
  const limitReached = multiple && max !== undefined && value.length >= max;

  function toggle(code) {
    if (!multiple) return onChange([code]);
    const next = value.includes(code) ? value.filter((v) => v !== code) : [...value, code];
    return onChange(next);
  }

  return (
    <div className={styles[variant]} role="group" aria-label={label} aria-describedby={describedBy}>
      {options.map((option) => {
        const selected = value.includes(option.code);
        const Icon = option.icon;
        return (
          <button
            key={option.code}
            type="button"
            aria-pressed={selected}
            disabled={limitReached && !selected}
            className={[styles.item, styles[`${variant}Item`], selected && styles.selected]
              .filter(Boolean)
              .join(' ')}
            onClick={() => toggle(option.code)}
          >
            {Icon && <Icon size={17} aria-hidden="true" />}
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
