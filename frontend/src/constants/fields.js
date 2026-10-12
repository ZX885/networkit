import { toOptions } from '../lib/options.js';

// Направления: FLDS из legacy (36) + «Other» в конце (отдельного поля для уточнения нет)
// prettier-ignore
export const FIELDS = [
  ...toOptions([
    'Accounting', 'Architecture', 'Artificial Intelligence', 'Biology', 'Biotechnology',
    'Business Administration', 'Chemistry', 'Civil Engineering', 'Computer Science', 'Data Science',
    'Design', 'Economics', 'Education', 'Electrical Engineering', 'Entrepreneurship',
    'Environmental Science', 'Finance', 'History', 'International Relations', 'Journalism', 'Law',
    'Literature', 'Marketing', 'Mathematics', 'Mechanical Engineering', 'Medicine', 'Music',
    'Neuroscience', 'Nursing', 'Philosophy', 'Physics', 'Political Science', 'Psychology',
    'Public Health', 'Sociology', 'Software Engineering',
  ]),
  { code: 'other', label: 'Other' },
];
