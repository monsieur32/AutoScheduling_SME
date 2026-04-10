import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    const savedTheme = localStorage.getItem('app-theme') || 'dark';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('app-theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <span style={{ fontSize: '1rem' }}>{theme === 'dark' ? '🌙' : '☀️'}</span>
      <label style={{
        position: 'relative',
        display: 'inline-block',
        width: '44px',
        height: '24px'
      }}>
        <input
          type="checkbox"
          checked={theme === 'light'}
          onChange={toggleTheme}
          style={{ opacity: 0, width: 0, height: 0 }}
        />
        <span style={{
          position: 'absolute',
          cursor: 'pointer',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: theme === 'dark' ? '#334155' : '#e2e8f0',
          transition: '.3s',
          borderRadius: '24px'
        }}>
          <span style={{
            position: 'absolute',
            content: '""',
            height: '18px',
            width: '18px',
            left: theme === 'light' ? '22px' : '4px',
            bottom: '3px',
            backgroundColor: theme === 'dark' ? '#fff' : '#0f172a',
            transition: '.3s',
            borderRadius: '50%'
          }} />
        </span>
      </label>
    </div>
  );
}
