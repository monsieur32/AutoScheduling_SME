import React, { useState } from 'react';

interface ExpanderProps {
  title: string;
  defaultExpanded?: boolean;
  children: React.ReactNode;
}

const Expander: React.FC<ExpanderProps> = ({ title, defaultExpanded = false, children }) => {
  const [isOpen, setIsOpen] = useState(defaultExpanded);

  return (
    <div className="expander">
      <div className="expander-header" onClick={() => setIsOpen(!isOpen)}>
        <span>{title}</span>
        <span className={`expander-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </div>
      {isOpen && (
        <div className="expander-content">
          {children}
        </div>
      )}
    </div>
  );
};

export default Expander;
