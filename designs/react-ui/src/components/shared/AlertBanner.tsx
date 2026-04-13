import React from 'react';

interface AlertBannerProps {
  type: 'success' | 'info' | 'warning' | 'error';
  children: React.ReactNode;
}

const icons: Record<string, string> = {
  success: '✅',
  info: 'ℹ️',
  warning: '⚠️',
  error: '❌'
};

const AlertBanner: React.FC<AlertBannerProps> = ({ type, children }) => {
  return (
    <div className={`alert alert-${type}`}>
      <span className="alert-icon">{icons[type]}</span>
      <div>{children}</div>
    </div>
  );
};

export default AlertBanner;
