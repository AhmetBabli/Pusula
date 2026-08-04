import React, { useState } from 'react';
import { X, Mail, Lock, User, Upload } from 'lucide-react';

function RegisterModal({ isOpen, onClose }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [cvFile, setCvFile] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Backend bağlantısı kurulacak
    console.log("Register attempt:", { name, email, password, cvFile });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content cyber-modal-content">
        <div className="modal-header">
          <h3 className="h-title">Hesap Oluştur</h3>
          <button className="modal-close cyber-modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <form onSubmit={handleSubmit} className="cyber-form">
            <div className="form-group">
              <label>Ad Soyad</label>
              <div className="input-with-icon">
                <User size={16} className="input-icon" />
                <input 
                  type="text" 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Örn: Ahmet Yılmaz"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>E-posta Adresi</label>
              <div className="input-with-icon">
                <Mail size={16} className="input-icon" />
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ornek@sirket.com"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Şifre</label>
              <div className="input-with-icon">
                <Lock size={16} className="input-icon" />
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>CV Yükle (İsteğe Bağlı)</label>
              <div 
                className={`custom-file-upload ${cvFile ? 'has-file' : ''}`}
                onClick={() => document.getElementById('cv-upload').click()}
              >
                <Upload size={24} className="upload-icon" />
                <div className="upload-text">
                  {cvFile ? (
                    <span className="file-name">{cvFile.name}</span>
                  ) : (
                    <>
                      <strong>CV'nizi buraya sürükleyin</strong>
                      <span>veya tıklayarak dosya seçin</span>
                    </>
                  )}
                </div>
                <input 
                  id="cv-upload"
                  type="file" 
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => setCvFile(e.target.files[0])}
                  hidden
                />
              </div>
            </div>

            <div className="form-actions" style={{ marginTop: '30px' }}>
              <button type="submit" className="auth-btn solid large" style={{ width: '100%' }}>
                Kayıt Ol ve Başla
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default RegisterModal;
