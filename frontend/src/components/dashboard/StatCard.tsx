import React from 'react';

const COLOR_STYLES = {
  primary: { text: 'text-primary', bg: 'bg-primary-container/10', border: 'border-primary-container/20' },
  secondary: { text: 'text-secondary', bg: 'bg-secondary/10', border: 'border-secondary/20' },
  warning: { text: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/20' },
  success: { text: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20' },
  danger: { text: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/20' },
};

function StatCard({ icon: Icon, label, value, color = 'primary', onClick }) {
  const style = COLOR_STYLES[color] || COLOR_STYLES.primary;

  return (
    <div
      onClick={onClick}
      className={`bg-surface-container border border-outline-variant/10 rounded-2xl p-5 flex items-center gap-4 transition-all duration-300 ${
        onClick ? 'cursor-pointer hover:border-outline-variant/20 hover:-translate-y-0.5' : ''
      }`}
    >
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 border ${style.bg} ${style.border} ${style.text}`}>
        <Icon size={22} />
      </div>
      <div className="min-w-0">
        <div className={`text-2xl font-display font-semibold ${style.text}`}>{value}</div>
        <div className="text-xs font-label text-on-surface-variant tracking-wider uppercase truncate">{label}</div>
      </div>
    </div>
  );
}

export default StatCard;
