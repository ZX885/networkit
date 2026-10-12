import { useNavigate } from 'react-router-dom';
import Button from '../../../../components/ui/Button.jsx';
import { texts } from '../../../../texts/en.js';
import AuthCard from '../AuthCard.jsx';
import ResendEmail from '../ResendEmail.jsx';

const t = texts.register.checkEmail;

// Экран после регистрации: просим подтвердить почту; письмо можно запросить повторно.
export default function CheckEmail({ email }) {
  const navigate = useNavigate();

  return (
    <AuthCard title={t.title} subtitle={t.text(email)}>
      <ResendEmail email={email} />
      <Button fullWidth onClick={() => navigate('/login')}>
        {t.back}
      </Button>
    </AuthCard>
  );
}
