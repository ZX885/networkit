import { Component } from 'react';
import ErrorFallback from './ErrorFallback.jsx';

const STAMP_KEY = 'networkit:last-render-error';
const REPEAT_WINDOW_MS = 60_000;

// Ошибка повторилась, если прошлая случилась меньше минуты назад (например, после «Reload»)
function checkRepeated() {
  try {
    const previous = Number(sessionStorage.getItem(STAMP_KEY));
    sessionStorage.setItem(STAMP_KEY, String(Date.now()));
    return previous > 0 && Date.now() - previous < REPEAT_WINDOW_MS;
  } catch {
    return false; // sessionStorage может быть недоступен
  }
}

// Ловит ошибки рендера внутри себя: вместо пустого экрана — «Something went wrong» и кнопка «Reload».
// Ошибку пишем в консоль; пользователю технические детали не показываем.
// inLayout — внутри оболочки приложения (сайдбар остаётся на месте).
export default class ErrorBoundary extends Component {
  state = { failed: false, repeated: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    console.error(error, info.componentStack);
    this.setState({ repeated: checkRepeated() }); // здесь, а не в getDerivedStateFromError: React может вызвать тот дважды
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return <ErrorFallback repeated={this.state.repeated} inLayout={this.props.inLayout} />;
  }
}
