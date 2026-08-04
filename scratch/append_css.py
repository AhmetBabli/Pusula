import os

css_content = """
/* ============================================================
   NEW STYLES (Navigation, Empty States, Job Meta)
   ============================================================ */

/* Navigation */
.nav-deck {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 30px 20px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-glow);
  width: 260px;
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 200;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 14px 20px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-dim);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-colors), var(--transition-transform);
  text-align: left;
  font-family: var(--font-heading);
  font-weight: 500;
  letter-spacing: 0.05em;
  position: relative;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-main);
  transform: translateX(4px);
}

.nav-link.active {
  background: var(--border-glow);
  color: var(--accent-primary);
  border-color: rgba(139, 92, 246, 0.3);
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.15);
}

.nav-link.active .dot {
  content: '';
  position: absolute;
  right: 15px;
  width: 8px;
  height: 8px;
  background: var(--accent-primary);
  border-radius: 50%;
  box-shadow: 0 0 10px var(--accent-primary);
}

.nav-icon {
  color: inherit;
}

/* Empty States */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  min-height: 300px;
}

.empty-icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  border: 1px solid var(--border-glow);
  box-shadow: var(--glow-primary);
}

.empty-icon {
  color: var(--accent-primary);
}

.empty-title {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-vibrant);
  margin-bottom: 12px;
}

.empty-desc {
  color: var(--text-dim);
  max-width: 400px;
  line-height: 1.6;
}

/* Job Meta Items */
.job-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  color: var(--text-dim);
  font-size: 0.9rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-icon {
  color: var(--accent-secondary);
}

.meta-separator {
  color: rgba(255, 255, 255, 0.2);
  font-size: 0.8rem;
}

.job-source {
  background: rgba(255, 255, 255, 0.05);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  color: var(--text-main);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
"""

css_path = r"c:\Users\ahmet\OneDrive - DOĞUŞ ÜNİVERSİTESİ\Masaüstü\Kariyer-Ajanı\frontend\src\index.css"

with open(css_path, "a", encoding="utf-8") as f:
    f.write(css_content)

print("CSS appended successfully.")
