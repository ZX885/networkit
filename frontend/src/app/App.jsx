import AuthProvider from './providers/AuthProvider.jsx';
import ThemeProvider from './providers/ThemeProvider.jsx';
import ToastProvider from '../components/ui/ToastProvider.jsx';
import ErrorBoundary from '../components/shared/ErrorBoundary.jsx';
import AppRouter from './router.jsx';

// Корень приложения: глобальные провайдеры (тема, тосты, вход) + маршруты
export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <ErrorBoundary>
            <AppRouter />
          </ErrorBoundary>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}
