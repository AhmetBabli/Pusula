import React from 'react';

export default function HandTitle({ 
  as: Tag = 'h2', // Polymorphic Prop: Varsayılan h2, ama h1 veya h3 olarak da çağrılabilir
  children, 
  highlight = false, 
  highlightColor = 'yellow', 
  size, // Artık opsiyonel, inline vermek yerine CSS kullanmak daha sağlıklı
  className = '',
  style = {},
  ...rest // Geriye kalan tüm özellikleri DOM'a aktar
}) {
  return (
    <Tag 
      className={`section-title ${className}`.trim()} 
      // Eğer size prop'u verilmişse CSS değişkeni olarak aktar, böylece medya sorguları (media query) ile ezilebilir
      style={{ 
        ...(size ? { '--title-size': size, fontSize: 'var(--title-size)' } : {}), 
        ...style 
      }}
      {...rest}
    >
      {children}
      
      {highlight && (
        <span 
          className="highlight" 
          aria-hidden="true" // A11y: Ekran okuyucular bu boş dekoratif etiketi görmezden gelir
          style={highlightColor !== 'yellow' ? { background: `var(--highlight-${highlightColor})` } : {}}
        />
      )}
    </Tag>
  );
}