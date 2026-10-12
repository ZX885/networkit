import Tag from '../../../components/ui/Tag.jsx';
import { labelsOf } from '../../../lib/labels.js';
import styles from './TagList.module.css';

// Список тегов из кодов справочника: code → label (сырые коды не показываем)
export default function TagList({ list, codes }) {
  return (
    <ul className={`${styles.list} user-text`}>
      {labelsOf(list, codes).map((label) => (
        <li key={label}>
          <Tag>{label}</Tag>
        </li>
      ))}
    </ul>
  );
}
