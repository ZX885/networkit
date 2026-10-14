import useMeta from '../api/useMeta.js';
import MetaGate from '../components/shared/MetaGate.jsx';
import Logo from '../components/ui/Logo.jsx';
import CheckEmail from '../features/auth/components/register/CheckEmail.jsx';
import RegisterWizard from '../features/auth/components/register/RegisterWizard.jsx';
import useRegisterForm from '../features/auth/hooks/useRegisterForm.js';
import styles from './RegisterPage.module.css';

// Рамка страницы регистрации: логотип и контейнер (у экрана «Check your email» своя карточка)
function RegisterFrame({ children }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.container}>
        <div className={styles.logo}>
          <Logo />
        </div>
        {children}
      </div>
    </div>
  );
}

// Мастер создаётся, когда справочники сервера уже загружены: введённые данные не теряются
// при повторной загрузке, а списки не бывают пустыми.
function RegisterFlow() {
  const { meta } = useMeta();
  const form = useRegisterForm(meta.limits);

  if (form.registeredEmail) return <CheckEmail email={form.registeredEmail} />;

  return (
    <RegisterFrame>
      <RegisterWizard form={form} />
    </RegisterFrame>
  );
}

// Страница регистрации: мастер из 8 шагов, после отправки — экран «Check your email».
// Страны, направления и лимиты берутся с сервера (GET /api/meta/): пока грузятся — индикатор,
// при ошибке — сообщение с кнопкой «Try again».
export default function RegisterPage() {
  return (
    <MetaGate wrapper={RegisterFrame}>
      <RegisterFlow />
    </MetaGate>
  );
}
