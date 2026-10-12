import AppLayout from '../../components/layout/AppLayout.jsx';
import Navbar from '../../components/layout/Navbar.jsx';
import PageLoader from '../../components/layout/PageLoader.jsx';
import AppNotFoundPage from '../../pages/AppNotFoundPage.jsx';
import NotFoundPage from '../../pages/NotFoundPage.jsx';
import useAuth from '../providers/useAuth.js';

// Неизвестный адрес: вошедший видит 404 внутри приложения (с сайдбаром), гость — обычную 404
export default function NotFoundRoute() {
  const { status } = useAuth();

  if (status === 'loading') return <PageLoader />;
  if (status === 'authenticated') {
    return (
      <AppLayout>
        <AppNotFoundPage />
      </AppLayout>
    );
  }
  return (
    <>
      <Navbar />
      <NotFoundPage />
    </>
  );
}
