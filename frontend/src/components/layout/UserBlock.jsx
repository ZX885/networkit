import { Link } from 'react-router-dom';
import { fullName } from '../../lib/labels.js';
import Avatar from '../ui/Avatar.jsx';
import styles from './UserBlock.module.css';

// Блок пользователя внизу сайдбара (legacy .sb-user): аватар, имя, статус; ведёт в «My profile».
export default function UserBlock({ user }) {
  return (
    <Link to="/me" className={styles.block}>
      <Avatar
        id={user.username}
        firstName={user.first_name}
        lastName={user.last_name}
        src={user.avatar_url}
        size="sm"
      />
      <span className={styles.text}>
        <span className={`${styles.name} user-text`}>{fullName(user)}</span>
        <span className={styles.role}>{user.status_label}</span>
      </span>
    </Link>
  );
}
