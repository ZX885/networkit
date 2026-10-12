import PersonCard from '../../../components/shared/PersonCard.jsx';
import styles from './PeopleGrid.module.css';

const SKELETON_COUNT = 6;

// Сетка карточек (legacy .rg-grid). Пока данные грузятся (people = null), показывает скелетоны.
// onSavedChange передаётся дальше в карточку (Saved убирает снятые с закладки).
export default function PeopleGrid({ people, onSavedChange }) {
  if (!people) {
    return (
      <div className={styles.grid} aria-hidden="true">
        {Array.from({ length: SKELETON_COUNT }, (_, index) => (
          <div key={index} className={styles.skeleton} />
        ))}
      </div>
    );
  }

  return (
    <div className={styles.grid}>
      {people.map((person) => (
        <PersonCard key={person.username} person={person} onSavedChange={onSavedChange} />
      ))}
    </div>
  );
}
