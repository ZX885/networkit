import { useNavigate } from 'react-router-dom';
import useToast from '../components/ui/useToast.js';
import AuthCard from '../features/auth/components/AuthCard.jsx';
import LoginForm from '../features/auth/components/LoginForm.jsx';
import { texts } from '../texts/en.js';

const t = texts.login;

// Страница входа. После успешного входа — тост и переход в приложение (Discover).
export default function LoginPage() {
  const navigate = useNavigate();
  const showToast = useToast();

  function handleSuccess(user) {
    showToast(t.welcome(user.first_name), 'success');
    navigate('/discover');
  }

  return (
    <AuthCard title={t.title} subtitle={t.subtitle}>
      <LoginForm onSuccess={handleSuccess} />
    </AuthCard>
  );
}
