import React from 'react';

export default function Highlighter({ 
  color = 'yellow', 
  className = '', 
  children, 
  ...rest // Geriye kalan tüm özellikleri (props) topla
}) {
  return (
    <span 
      className={`highlighter ${color} ${className}`.trim()} 
      {...rest} // Topladığın özellikleri DOM elementine aktar
    >
      {children}
    </span>
  );
}