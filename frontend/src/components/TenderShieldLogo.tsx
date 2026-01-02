import React from 'react';

/**
 * Официальная эмблема системы «Тендер.Щит»
 * Круглый логотип с текстом по кругу, щитом и весами правосудия
 */
const TenderShieldLogo: React.FC<{ className?: string }> = ({ className = 'w-12 h-12' }) => {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      xmlnsXlink="http://www.w3.org/1999/xlink"
    >
      {/* Внешнее кольцо */}
      <circle cx="32" cy="32" r="30" fill="#1a3b5c" stroke="#c4a77d" strokeWidth="2"/>
      
      {/* Щит */}
      <path d="M32 6 L12 16 V28 C12 40 20 52 32 58 C44 52 52 40 52 28 V16 L32 6Z" fill="#c4a77d" stroke="#1a3b5c" strokeWidth="1"/>
      
      {/* Весы правосудия */}
      <g fill="#1a3b5c">
        <rect x="31" y="20" width="2" height="20" />
        <rect x="18" y="24" width="28" height="2" />
        <path d="M20 26 L16 34 H24 L20 26Z" />
        <path d="M44 26 L40 34 H48 L44 26Z" />
        <rect x="26" y="40" width="12" height="2" />
      </g>

      {/* Текст по кругу */}
      <path id="curve" d="M14,32 a18,18 0 1,1 36,0" fill="none" />
      <text width="64" fontFamily="Arial, sans-serif" fontSize="6" fontWeight="bold" fill="#c4a77d">
        <textPath href="#curve" startOffset="50%" textAnchor="middle">
          ТЕНДЕР.ЩИТ
        </textPath>
      </text>
    </svg>
  );
};

export default TenderShieldLogo;
