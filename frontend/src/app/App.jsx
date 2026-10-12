import AuthProvider from './providers/AuthProvider.jsx';
import ThemeProvider from './providers/ThemeProvider.jsx';
import ToastProvider from '../components/ui/ToastProvider.jsx';
import AppRouter from './router.jsx';

// Корень приложения: глобальные провайдеры (тема, тосты, вход) + маршруты
export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}
