import React, { useState } from 'react';
import { X, Mail, Lock } from 'lucide-react';

function LoginModal({ isOpen, onClose }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Backend bağlantısı kurulacak
    console.log("Login attempt:", { email, password });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content cyber-modal-content">
        <div className="modal-header">
          <h3 className="h-title">Giriş Yap</h3>
          <button className="modal-close cyber-modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <form onSubmit={handleSubmit} className="cyber-form">
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

            <div className="form-actions" style={{ marginTop: '30px' }}>
              <button type="submit" className="auth-btn solid large" style={{ width: '100%' }}>
                Oturum Aç
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default LoginModal;
