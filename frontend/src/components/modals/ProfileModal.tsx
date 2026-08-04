import React, { useState, useEffect } from 'react';
import CyberModal from '../ui/CyberModal';
import { User, Save } from 'lucide-react';

function ProfileModal({ isOpen, onClose, profile, onSave, isLoading }) {
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    university: '',
    department: '',
    phone: '',
    linkedin_url: '',
    github_url: '',
    summary: ''
  });

  // Modal her açıldığında veya profil değiştiğinde formu temizle (Reset)
  useEffect(() => {
    if (isOpen && profile) {
      setForm({
        full_name: profile.full_name || '',
        email: profile.email || '',
        university: profile.university || '',
        department: profile.department || '',
        phone: profile.phone || '',
        linkedin_url: profile.linkedin_url || '',
        github_url: profile.github_url || '',
        summary: profile.summary || ''
      });
    }
  }, [isOpen, profile]);

  // Tek bir merkezi fonksiyonla tüm inputları yönet
  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  // Form submit olduğunda sayfa yenilenmesini engelle (e.preventDefault())
  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <CyberModal isOpen={isOpen} onClose={onClose} title="PROFİL AYARLARI">
      {/* 1. HTML Form etiketini ekledik ve onSubmit olayını bağladık */}
      <form onSubmit={handleSubmit} className="modal-inner profile-form">
        
        <div className="profile-avatar">
          <User size={40} />
        </div>
        
        {/* 2. Etiketler (A11y) ve name="" attribute'leri eklendi */}
        <fieldset style={{ border: 'none', margin: 0, padding: 0 }}>
          <legend className="form-section-title">Kişisel Bilgiler</legend>
          <div className="form-row">
            <input 
              name="full_name"
              className="cmd-input" 
              value={form.full_name} 
              onChange={handleChange} 
              placeholder="Ad Soyad"
              aria-label="Ad Soyad"
              required // Önemli alanlar için HTML validasyonu
            />
            <input 
              name="email"
              className="cmd-input" 
              value={form.email} 
              onChange={handleChange} 
              placeholder="E-posta"
              type="email"
              aria-label="E-posta"
              required
            />
          </div>
        </fieldset>
        
        <fieldset style={{ border: 'none', margin: 0, padding: 0 }}>
          <legend className="form-section-title">Eğitim</legend>
          <div className="form-row">
            <input 
              name="university"
              className="cmd-input" 
              value={form.university} 
              onChange={handleChange} 
              placeholder="Üniversite"
              aria-label="Üniversite"
            />
            <input 
              name="department"
              className="cmd-input" 
              value={form.department} 
              onChange={handleChange} 
              placeholder="Bölüm"
              aria-label="Bölüm"
            />
          </div>
        </fieldset>

        <fieldset style={{ border: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <legend className="form-section-title">İletişim & Linkler</legend>
          <input 
            name="phone"
            className="cmd-input" 
            value={form.phone} 
            onChange={handleChange} 
            placeholder="Telefon (Örn: +90 555...)"
            type="tel"
            aria-label="Telefon Numarası"
          />
          <input 
            name="linkedin_url"
            className="cmd-input" 
            value={form.linkedin_url} 
            onChange={handleChange} 
            placeholder="LinkedIn URL"
            type="url"
            aria-label="LinkedIn Profili"
          />
          <input 
            name="github_url"
            className="cmd-input" 
            value={form.github_url} 
            onChange={handleChange} 
            placeholder="GitHub URL"
            type="url"
            aria-label="GitHub Profili"
          />
          <textarea 
            name="summary"
            className="cmd-input" 
            rows="3"
            value={form.summary} 
            onChange={handleChange} 
            placeholder="Kısa biyografi... (Kimsiniz, ne yaparsınız?)"
            aria-label="Kısa Biyografi"
          />
        </fieldset>
        
        {/* Buton type="submit" yapıldı */}
        <button 
          type="submit"
          className="cmd-btn cmd-btn-primary full-width" 
          disabled={isLoading}
        >
          <Save size={16} /> {isLoading ? 'KAYDEDİLİYOR...' : 'KAYDET'}
        </button>
      </form>
    </CyberModal>
  );
}

export default ProfileModal;