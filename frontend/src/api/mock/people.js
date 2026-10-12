// MOCK: вымышленные люди для Discover, Saved и страницы профиля. Заменим реальными запросами
// GET /api/profiles/, /api/profiles/{username}/, /api/saved/ в шагах B4–B7.
// Формат Card — по docs/SPEC.md §3.6; для страницы профиля добавлены поля формата Public.
import { fieldLabel } from '../../lib/labels.js';
import { sleep } from './delay.js';

export const PAGE_SIZE = 12;

// prettier-ignore
const PEOPLE = [
  { username: 'amina_k', first_name: 'Amina', last_name: 'Karimova', field: 'computer_science', status: 'student', city: 'Tashkent', country: 'UZ', university: 'WIUT', region: 'Tashkent', year_level: '3rd year', bio: 'Building small tools for students. Looking for a study partner for algorithms and someone to hack with on weekends.', interests: ['computer_science', 'artificial_intelligence', 'design'], languages: ['english', 'uzbek', 'russian'], goals: ['study_partners', 'project_collaborators'], contacts: { telegram: '@amina_k', instagram: '', whatsapp: '', linkedin: 'linkedin.com/in/aminak', public_email: '' }, joined: '2026-09' },
  { username: 'timur_b', first_name: 'Timur', last_name: 'Bekov', field: 'finance', status: 'professional', city: 'Samarkand', country: 'UZ', university: 'SamSU', region: 'Samarkand', year_level: 'Analyst', bio: 'Analyst at a regional bank. Happy to mentor anyone curious about finance careers.', interests: ['finance', 'economics', 'entrepreneurship'], languages: ['english', 'uzbek', 'russian'], goals: ['mentorship', 'career_networking'], contacts: { telegram: '@timur_b', instagram: '', whatsapp: '', linkedin: '', public_email: 'timur@example.com' }, joined: '2026-08' },
  { username: 'sofia_m', first_name: 'Sofia', last_name: 'Martins', field: 'design', status: 'student', city: 'Lisbon', country: 'PT', university: 'IADE', region: 'Lisbon', year_level: '2nd year', bio: 'Product design student exploring accessibility. Supercalifragilisticexpialidocious_longwordtotestwrapping_aaaaaaaaaaaaaaaaaaaaaaaaaaaa', interests: ['design', 'psychology', 'marketing'], languages: ['english', 'portuguese', 'spanish'], goals: ['project_collaborators', 'cv_portfolio'], contacts: { telegram: '', instagram: '@sofia.designs', whatsapp: '', linkedin: '', public_email: '' }, joined: '2026-09' },
  { username: 'daniyar_s', first_name: 'Daniyar', last_name: 'Seitkali', field: 'software_engineering', status: 'professional', city: 'Almaty', country: 'KZ', university: '', region: 'Almaty', year_level: 'Senior Dev', bio: 'Backend developer, open-source contributor. Open to co-founding something small and useful.', interests: ['computer_science', 'entrepreneurship'], languages: ['english', 'kazakh', 'russian'], goals: ['startup_cofounders', 'project_collaborators'], contacts: { telegram: '@daniyar_s', instagram: '', whatsapp: '', linkedin: 'linkedin.com/in/daniyars', public_email: '' }, joined: '2026-07' },
  { username: 'laura_h', first_name: 'Laura', last_name: 'Hansen', field: 'biology', status: 'student', city: 'Copenhagen', country: 'DK', university: 'University of Copenhagen', region: 'Capital Region', year_level: 'Master 1st year', bio: 'Studying molecular biology. Interested in research collaboration and science communication.', interests: ['biology', 'chemistry', 'biotechnology'], languages: ['english', 'danish', 'german'], goals: ['research_collaboration', 'study_partners'], contacts: { telegram: '', instagram: '', whatsapp: '', linkedin: 'linkedin.com/in/laurah', public_email: '' }, joined: '2026-06' },
  { username: 'rustam_a', first_name: 'Rustam', last_name: 'Aliev', field: 'law', status: 'student', city: 'Tashkent', country: 'UZ', university: 'TSUL', region: 'Tashkent', year_level: '4th year', bio: 'Law student preparing for an LLM abroad. Happy to swap application tips.', interests: ['law', 'political_science', 'history'], languages: ['english', 'uzbek', 'russian'], goals: ['college_prep', 'friends'], contacts: { telegram: '@rustam_a', instagram: '', whatsapp: '', linkedin: '', public_email: '' }, joined: '2026-09' },
  { username: 'mei_chen', first_name: 'Mei', last_name: 'Chen', field: 'data_science', status: 'professional', city: 'Singapore', country: 'SG', university: 'NUS', region: '', year_level: 'Data Analyst', bio: 'Data analyst who loves turning messy spreadsheets into stories.', interests: ['computer_science', 'mathematics', 'artificial_intelligence'], languages: ['english', 'chinese'], goals: ['career_networking', 'mentorship'], contacts: { telegram: '', instagram: '', whatsapp: '', linkedin: 'linkedin.com/in/meichen', public_email: 'mei@example.com' }, joined: '2026-05' },
  { username: 'omar_h', first_name: 'Omar', last_name: 'Haddad', field: 'mechanical_engineering', status: 'student', city: 'Cairo', country: 'EG', university: 'Cairo University', region: 'Cairo', year_level: '3rd year', bio: 'Robotics club member. Looking for teammates for a university competition.', interests: ['engineering', 'physics', 'mathematics'], languages: ['english', 'arabic'], goals: ['project_collaborators', 'internship_opportunities'], contacts: { telegram: '', instagram: '@omar.builds', whatsapp: '', linkedin: '', public_email: '' }, joined: '2026-08' },
  { username: 'nilufar_r', first_name: 'Nilufar', last_name: 'Rakhimova', field: 'marketing', status: 'professional', city: 'Tashkent', country: 'UZ', university: '', region: 'Tashkent', year_level: 'Marketing Lead', bio: 'Marketing lead at a young startup. Always up for a coffee chat about growth.', interests: ['marketing', 'entrepreneurship', 'design'], languages: ['english', 'uzbek', 'russian'], goals: ['career_networking', 'startup_cofounders'], contacts: { telegram: '@nilufar_r', instagram: '', whatsapp: '', linkedin: '', public_email: '' }, joined: '2026-07' },
  { username: 'lucas_f', first_name: 'Lucas', last_name: 'Ferreira', field: 'architecture', status: 'student', city: 'São Paulo', country: 'BR', university: 'USP', region: 'São Paulo', year_level: '5th year', bio: 'Architecture student fascinated by sustainable materials.', interests: ['architecture', 'design', 'history'], languages: ['english', 'portuguese'], goals: ['cv_portfolio', 'friends'], contacts: { telegram: '', instagram: '', whatsapp: '', linkedin: '', public_email: '' }, joined: '2026-04' },
  { username: 'zarina_t', first_name: 'Zarina', last_name: 'Tursunova', field: 'psychology', status: 'student', city: 'Bishkek', country: 'KG', university: 'AUCA', region: 'Bishkek', year_level: '2nd year', bio: 'Psychology student, volunteer at a youth helpline.', interests: ['psychology', 'sociology', 'literature'], languages: ['english', 'kyrgyz', 'russian'], goals: ['friends', 'study_partners'], contacts: { telegram: '@zarina_t', instagram: '', whatsapp: '', linkedin: '', public_email: '' }, joined: '2026-09' },
  { username: 'james_o', first_name: 'James', last_name: 'Okafor', field: 'economics', status: 'professional', city: 'Lagos', country: 'NG', university: '', region: 'Lagos', year_level: 'Economist', bio: 'Economist working on development projects. Mentoring early-career researchers.', interests: ['economics', 'political_science', 'finance'], languages: ['english', 'yoruba'], goals: ['mentorship', 'research_collaboration'], contacts: { telegram: '', instagram: '', whatsapp: '', linkedin: 'linkedin.com/in/jamesokafor', public_email: '' }, joined: '2026-03' },
  { username: 'elif_y', first_name: 'Elif', last_name: 'Yilmaz', field: 'medicine', status: 'student', city: 'Istanbul', country: 'TR', university: 'Istanbul University', region: 'Istanbul', year_level: '4th year', bio: 'Medical student interested in neuroscience research.', interests: ['medicine', 'neuroscience', 'biology'], languages: ['english', 'turkish'], goals: ['research_collaboration', 'study_partners'], contacts: { telegram: '', instagram: '@elif.med', whatsapp: '', linkedin: '', public_email: '' }, joined: '2026-06' },
  { username: 'ivan_p', first_name: 'Ivan', last_name: 'Petrov', field: 'physics', status: 'student', city: 'Berlin', country: 'DE', university: 'TU Berlin', region: 'Berlin', year_level: 'PhD, 1st year', bio: 'PhD student in condensed matter physics. Open to chat about grad school.', interests: ['physics', 'mathematics', 'chemistry'], languages: ['english', 'german', 'russian'], goals: ['mentorship', 'research_collaboration'], contacts: { telegram: '', instagram: '', whatsapp: '', linkedin: '', public_email: 'ivan@example.com' }, joined: '2026-02' },
];

// Кто уже в избранном (меняется при нажатии на закладку, пока открыта вкладка)
const savedSet = new Set(['amina_k', 'daniyar_s']);

function toCard(person) {
  return {
    username: person.username,
    first_name: person.first_name,
    last_name: person.last_name,
    avatar_url: null,
    field: person.field,
    field_label: fieldLabel(person.field),
    status: person.status,
    city: person.city,
    country: person.country,
    bio: person.bio,
    interests: person.interests,
    is_saved: savedSet.has(person.username),
  };
}

// Поиск как на сервере: q — по имени, username и направлению; фильтры — точное совпадение кодов
export async function searchPeople({ q = '', country, field, status, goal, language, page = 1 }) {
  await sleep(350);
  const needle = q.trim().toLowerCase();
  const found = PEOPLE.filter((p) => {
    if (needle) {
      const haystack = `${p.first_name} ${p.last_name} ${p.username} ${p.field} ${p.university}`
        .toLowerCase()
        .replace(/_/g, ' ');
      if (!haystack.includes(needle)) return false;
    }
    if (country && p.country !== country) return false;
    if (field && p.field !== field) return false;
    if (status && p.status !== status) return false;
    if (goal && !p.goals.includes(goal)) return false;
    if (language && !p.languages.includes(language)) return false;
    return true;
  });
  const start = (page - 1) * PAGE_SIZE;
  return {
    count: found.length,
    pageCount: Math.max(1, Math.ceil(found.length / PAGE_SIZE)),
    results: found.slice(start, start + PAGE_SIZE).map(toCard),
  };
}

// Публичный профиль; null — такого username нет (страница «Profile not found»)
export async function getPublicProfile(username) {
  await sleep(300);
  const person = PEOPLE.find((p) => p.username === username);
  if (!person) return null;
  return { ...person, ...toCard(person), is_minor: false };
}

export async function listSavedPeople() {
  await sleep(300);
  return PEOPLE.filter((p) => savedSet.has(p.username)).map(toCard);
}

// Закладка: PUT/DELETE /api/saved/{username}/ (идемпотентно)
export async function setSaved(username, saved) {
  await sleep(150);
  if (saved) savedSet.add(username);
  else savedSet.delete(username);
}
