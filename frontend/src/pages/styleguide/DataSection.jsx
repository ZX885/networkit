import { useState } from 'react';
import Avatar from '../../components/ui/Avatar.jsx';
import Pagination from '../../components/ui/Pagination.jsx';
import Tag from '../../components/ui/Tag.jsx';
import Section from './Section.jsx';
import layout from './Section.module.css';

const PEOPLE = [
  { id: '3f2a9c1e-7b4d-4e8a-9c2f-1a6d5b8e0f31', first: 'Jane', last: 'Doe' },
  { id: '8b7e2d04-5c1a-4f3b-a9d6-2e4c7f1b9a05', first: 'Alex', last: 'Kim' },
  { id: 'c1d94a7f-3e2b-4a8c-b5f0-6d9e1a2c4b78', first: 'Maria', last: 'Sokolova' },
  { id: '5e0a8b3c-9d17-4c26-8f4e-b3a1d7c92e60', first: 'Timur', last: '' },
  { id: 'a47c1f95-2b3e-4d80-9e6a-0c5d8b1f3a29', first: 'Zarina', last: 'Karimova' },
];

// Аватары, теги, пагинация
export default function DataSection() {
  const [page, setPage] = useState(5);

  return (
    <Section title="Avatar, Tag, Pagination">
      <p className={layout.caption}>Avatar — sizes</p>
      <div className={layout.row}>
        {['sm', 'md', 'lg', 'xl'].map((size) => (
          <Avatar
            key={size}
            id={PEOPLE[0].id}
            firstName="Jane"
            lastName="Doe"
            size={size}
            alt={size}
          />
        ))}
      </div>

      <p className={layout.caption}>Avatar — color by id, image fallback</p>
      <div className={layout.row}>
        {PEOPLE.map((p) => (
          <Avatar key={p.id} id={p.id} firstName={p.first} lastName={p.last} />
        ))}
        <Avatar id="broken" firstName="Broken" lastName="Image" src="/no-such-image.png" />
      </div>

      <p className={layout.caption}>Tag</p>
      <div className={layout.row}>
        <Tag>Computer Science</Tag>
        <Tag>Design</Tag>
        <Tag>Startup co-founders</Tag>
      </div>

      <p className={layout.caption}>Pagination</p>
      <Pagination
        page={page}
        pageCount={12}
        onChange={setPage}
        label="Pagination"
        prevLabel="Previous page"
        nextLabel="Next page"
        pageLabel={(n) => `Page ${n}`}
      />
    </Section>
  );
}
