// MOCK: диалоги и сообщения. Заменим на GET /api/conversations/ и /messages/ в шагах B6–B7.
// Формат — docs/SPEC.md §3.8–3.9. Состояние живёт в памяти вкладки; подписка нужна, чтобы бейдж
// непрочитанных в сайдбаре обновлялся, когда диалог открыт.
import { sleep } from './delay.js';

const HOUR = 3600 * 1000;
const ago = (hours) => new Date(Date.now() - hours * HOUR).toISOString();

let nextMessageId = 100;
const message = (mine, body, hours, seen = true) => ({
  id: nextMessageId++,
  sender_is_me: mine,
  body,
  created_at: ago(hours),
  seen_at: seen ? ago(hours - 0.1) : null,
});

// prettier-ignore
const conversations = [
  {
    id: 'c1',
    other_user: { username: 'amina_k', first_name: 'Amina', last_name: 'Karimova', avatar_url: null, field_label: 'Computer Science' },
    messages: [
      message(false, 'Hi! I saw your profile, we both like algorithms.', 52),
      message(true, 'Hey Amina! Yes, I am looking for a study partner for the exam.', 51.5),
      message(false, 'Great, want to meet online on Saturday?', 3, false),
      message(false, 'I can share my notes beforehand.', 2.9, false),
    ],
  },
  {
    id: 'c2',
    other_user: { username: 'timur_b', first_name: 'Timur', last_name: 'Bekov', avatar_url: null, field_label: 'Finance' },
    messages: [
      message(true, 'Hello Timur, could you share some advice about starting in finance?', 30),
      message(false, 'Sure! Start with an internship, even a short one helps a lot.', 28),
      message(true, 'Thank you, that is helpful.', 27.5, false),
    ],
  },
  {
    id: 'c3',
    other_user: { username: 'sofia_m', first_name: 'Sofia', last_name: 'Martins', avatar_url: null, field_label: 'Design' },
    messages: [
      message(false, 'Would you like to collaborate on an accessibility project?', 200),
      message(true, 'Definitely! Send me the details.', 199),
    ],
  },
  {
    id: 'c4',
    other_user: { username: 'omar_h', first_name: 'Omar', last_name: 'Haddad', avatar_url: null, field_label: 'Mechanical Engineering' },
    messages: [],
  },
];

const listeners = new Set();
let version = 0; // растёт при любом изменении: по нему экраны перезагружают данные
function emit() {
  version += 1;
  listeners.forEach((listener) => listener());
}

export const getMessagesVersion = () => version;

export function subscribeMessages(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

const unreadOf = (conversation) =>
  conversation.messages.filter((m) => !m.sender_is_me && !m.seen_at).length;

// Для бейджа в сайдбаре (GET /api/conversations/summary/ → unread_messages)
export const getUnreadTotal = () => conversations.reduce((sum, c) => sum + unreadOf(c), 0);

function summary(conversation) {
  const last = conversation.messages.at(-1) ?? null;
  return {
    id: conversation.id,
    other_user: conversation.other_user,
    last_message: last && {
      body: last.body,
      sender_is_me: last.sender_is_me,
      created_at: last.created_at,
    },
    unread_count: unreadOf(conversation),
    last_message_at: last?.created_at ?? null,
  };
}

export async function listConversations() {
  await sleep(300);
  return conversations
    .map(summary)
    .sort((a, b) => (b.last_message_at ?? '').localeCompare(a.last_message_at ?? ''));
}

// null — такого диалога нет
export async function getConversation(id) {
  await sleep(200);
  const conversation = conversations.find((c) => c.id === id);
  if (!conversation) return null;
  return { ...summary(conversation), messages: [...conversation.messages] };
}

// Входящие помечаются прочитанными (POST /conversations/{id}/read/)
export async function markRead(id) {
  const conversation = conversations.find((c) => c.id === id);
  if (!conversation) return;
  let changed = false;
  conversation.messages.forEach((m) => {
    if (!m.sender_is_me && !m.seen_at) {
      m.seen_at = new Date().toISOString();
      changed = true;
    }
  });
  if (changed) emit();
}

export async function sendMessage(id, body) {
  await sleep(300);
  const conversation = conversations.find((c) => c.id === id);
  if (!conversation) throw new Error('not_found');
  const created = {
    id: nextMessageId++,
    sender_is_me: true,
    body,
    created_at: new Date().toISOString(),
    seen_at: null,
  };
  conversation.messages.push(created);
  emit();
  return created;
}
