import { useEffect, useRef } from 'react';
import styles from './HeroCanvas.module.css';

const POINT_COUNT = 50;
const LINK_DISTANCE = 120;

function createPoints(width, height) {
  return Array.from({ length: POINT_COUNT }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.25,
    vy: (Math.random() - 0.5) * 0.25,
    r: Math.random() * 1.5 + 0.5,
  }));
}

// Фон hero: плавающие точки, соединённые линиями (как initCanvas в legacy).
// Анимация ставится на паузу, если вкладка скрыта или блок вне экрана,
// и не запускается при prefers-reduced-motion (рисуется один статичный кадр).
export default function HeroCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const color = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim();
    let width = 0;
    let height = 0;
    let points = [];
    let frameId = 0;
    let inView = true;

    function draw(move) {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = color;
      ctx.strokeStyle = color;
      ctx.lineWidth = 0.8;
      points.forEach((p, i) => {
        if (move) {
          p.x += p.vx;
          p.y += p.vy;
          if (p.x < 0 || p.x > width) p.vx *= -1;
          if (p.y < 0 || p.y > height) p.vy *= -1;
        }
        ctx.globalAlpha = 0.18;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
        for (let j = i + 1; j < points.length; j += 1) {
          const q = points[j];
          const distance = Math.hypot(p.x - q.x, p.y - q.y);
          if (distance < LINK_DISTANCE) {
            ctx.globalAlpha = 0.06 * (1 - distance / LINK_DISTANCE);
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
          }
        }
      });
    }

    function loop() {
      draw(true);
      frameId = requestAnimationFrame(loop);
    }

    // Запускаем или останавливаем анимацию по текущим условиям
    function update() {
      const shouldRun = inView && !document.hidden && !reduceMotion.matches;
      if (shouldRun && !frameId) frameId = requestAnimationFrame(loop);
      if (!shouldRun && frameId) {
        cancelAnimationFrame(frameId);
        frameId = 0;
      }
      if (!shouldRun) draw(false); // статичный кадр
    }

    function resize() {
      const parent = canvas.parentElement;
      width = canvas.width = parent.offsetWidth;
      height = canvas.height = parent.offsetHeight;
      points = createPoints(width, height);
      update();
    }

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas.parentElement);
    const intersectionObserver = new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting;
      update();
    });
    intersectionObserver.observe(canvas);
    document.addEventListener('visibilitychange', update);
    reduceMotion.addEventListener('change', update);

    return () => {
      cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      document.removeEventListener('visibilitychange', update);
      reduceMotion.removeEventListener('change', update);
    };
  }, []);

  return <canvas ref={canvasRef} className={styles.canvas} aria-hidden="true" />;
}
