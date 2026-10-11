import { useNavigate } from 'react-router-dom';
import Button from '../../../../components/ui/Button.jsx';
import { texts } from '../../../../texts/en.js';
import AuthCard from '../AuthCard.jsx';

const t = texts.register.checkEmail;

// Экран после регистрации: просим подтвердить почту.
export default function CheckEmail({ email }) {
  const navigate = useNavigate();

  return (
    <AuthCard title={t.title} subtitle={t.text(email)}>
      <Button fullWidth onClick={() => navigate('/login')}>
        {t.back}
      </Button>
    </AuthCard>
  );
}
