import { Navigate } from 'react-router-dom';
import PageLoader from '../../components/layout/PageLoader.jsx';
import Button from '../../components/ui/Button.jsx';
import EmptyState from '../../components/ui/EmptyState.jsx';
import { texts } from '../../texts/en.js';
import useAuth from '../providers/useAuth.js';

// Страницы для вошедших: гостя отправляем на вход. Это только навигация; права проверяет сервер.
export default function ProtectedRoute({ children }) {
  const { status, errorCode, refresh } = useAuth();

  if (status === 'loading') return <PageLoader />;
  if (status === 'error') {
    return (
      <EmptyState
        title={texts.auth.unavailableTitle}
        description={
          errorCode === 'network_error'
            ? texts.apiErrors.network_error
            : texts.apiErrors.server_error
        }
        action={<Button onClick={refresh}>{texts.auth.tryAgain}</Button>}
      />
    );
  }
  if (status === 'anonymous') return <Navigate to="/login" replace />;
  return children;
}
