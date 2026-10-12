import Logo from '../components/ui/Logo.jsx';
import CheckEmail from '../features/auth/components/register/CheckEmail.jsx';
import RegisterWizard from '../features/auth/components/register/RegisterWizard.jsx';
import useRegisterForm from '../features/auth/hooks/useRegisterForm.js';
import styles from './RegisterPage.module.css';

// Страница регистрации: мастер из 8 шагов, после отправки — экран «Check your email».
export default function RegisterPage() {
  const form = useRegisterForm();

  if (form.registeredEmail) return <CheckEmail email={form.registeredEmail} />;

  return (
    <div className={styles.wrap}>
      <div className={styles.container}>
        <div className={styles.logo}>
          <Logo />
        </div>
        <RegisterWizard form={form} />
      </div>
    </div>
  );
}
