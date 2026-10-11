// MOCK: имитация сетевой задержки. Заменяется настоящими запросами к API на следующих шагах.
export function sleep(ms = 600) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// MOCK: ошибка в том же виде, в каком её вернёт настоящий apiClient (поле code)
export class MockApiError extends Error {
  constructor(code, message = code) {
    super(message);
    this.code = code;
  }
}
