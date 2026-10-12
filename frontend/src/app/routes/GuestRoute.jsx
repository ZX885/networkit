import { Navigate } from 'react-router-dom';
import PageLoader from '../../components/layout/PageLoader.jsx';
import useAuth from '../providers/useAuth.js';

// Страницы для гостей (вход, регистрация): залогиненного отправляем в приложение.
export default function GuestRoute({ children }) {
  const { status } = useAuth();

  if (status === 'loading') return <PageLoader />;
  if (status === 'authenticated') return <Navigate to="/discover" replace />;
  return children; // anonymous, а при недоступном сервере форма всё равно покажет понятную ошибку
}
