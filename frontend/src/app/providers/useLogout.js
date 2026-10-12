import { useNavigate } from 'react-router-dom';
import useToast from '../../components/ui/useToast.js';
import { apiErrorText } from '../../lib/apiErrors.js';
import { texts } from '../../texts/en.js';
import useAuth from './useAuth.js';

// Выход: возвращает функцию, которая уводит на главную, завершает сессию и показывает тост.
// Сначала переходим на главную: иначе защищённая страница после выхода сама отправит на /login.
export default function useLogout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const showToast = useToast();

  return async function handleLogout() {
    navigate('/');
    try {
      await logout();
      showToast(texts.nav.loggedOut);
    } catch (error) {
      showToast(apiErrorText(error), 'error'); // например, нет связи: сессия на сервере осталась
    }
  };
}
