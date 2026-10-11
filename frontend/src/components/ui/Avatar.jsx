import { useState } from 'react';
import { getAvatarIndex, getInitials } from '../../lib/avatar.js';
import styles from './Avatar.module.css';

// Аватар: фото (src) или инициалы на градиенте, цвет зависит от id (как в legacy).
// size: sm (32) | md (44) | lg (72) | xl (80). alt — описание для скринридера;
// если рядом уже написано имя, alt можно не передавать (аватар станет декоративным).
export default function Avatar({ id, firstName, lastName, src, size = 'md', alt = '' }) {
  const [failed, setFailed] = useState(false); // фото не загрузилось → показываем инициалы
  const showImage = src && !failed;

  return (
    <span
      className={[styles.avatar, styles[size]].join(' ')}
      style={{ background: `var(--avatar-${getAvatarIndex(id)})` }}
      role={alt ? 'img' : undefined}
      aria-label={alt || undefined}
      aria-hidden={alt ? undefined : true}
    >
      {showImage ? (
        <img className={styles.image} src={src} alt="" onError={() => setFailed(true)} />
      ) : (
        getInitials(firstName, lastName)
      )}
    </span>
  );
}
