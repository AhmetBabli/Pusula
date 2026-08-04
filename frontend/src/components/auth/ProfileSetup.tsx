import React, { useState } from 'react';
import { Linkedin, Mail, ArrowRight, GraduationCap, BookOpen, Check } from 'lucide-react';

export interface UserProfile {
  linkedin: string;
  imapEmail: string;
  university: string;
  major: string;
  interests: string[];
}

interface ProfileSetupProps {
  onComplete: (profile: UserProfile | null) => void;
}

const AVAILABLE_INTERESTS = [
  'Yapay Zeka (AI)', 'Frontend', 'Backend', 'Data Science', 
  'Product Management', 'DevOps', 'Cyber Security', 'UI/UX Design', 'Mobil Geliştirme'
];

const UNIVERSITIES = [
  'Boğaziçi Üniversitesi', 'ODTÜ', 'İTÜ', 'Bilkent Üniversitesi', 
  'Koç Üniversitesi', 'Sabancı Üniversitesi', 'Yıldız Teknik Üniversitesi', 
  'Doğuş Üniversitesi', 'Diğer'
];

export const ProfileSetup: React.FC<ProfileSetupProps> = ({ onComplete }) => {
  const [step, setStep] = useState<1 | 2>(1);
  const [formData, setFormData] = useState<UserProfile>({
    linkedin: '',
    imapEmail: '',
    university: '',
    major: '',
    interests: []
  });

  const toggleInterest = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const handleNext = () => {
    if (step === 1) setStep(2);
    else onComplete(formData);
  };

  const handleSkip = () => {
    onComplete(null);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#09090B] text-white px-6 relative overflow-hidden animate-[fadeIn_0.5s_ease-out]">
      {/* Background Grid */}
      <div className="fixed inset-0 pointer-events-none z-0 opacity-[0.015]"
        style={{ backgroundImage: 'linear-gradient(to right,#fff 1px,transparent 1px),linear-gradient(to bottom,#fff 1px,transparent 1px)', backgroundSize: '48px 48px' }} />

      {/* Subtle Glow */}
      <div className="absolute top-[10%] left-[50%] -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-blue-600/5 blur-[120px] pointer-events-none z-0" />

      {/* Skip Button Top Right */}
      <button 
        onClick={handleSkip}
        className="absolute top-8 right-8 z-20 text-[11px] font-mono text-gray-500 hover:text-white tracking-widest uppercase transition-colors"
      >
        Daha Sonra
      </button>

      <div className="relative z-10 w-full max-w-xl">
        <div className="text-center mb-10">
          <div className="text-[10px] font-mono text-blue-500 tracking-[0.2em] mb-4 uppercase border border-blue-500/20 inline-block px-3 py-1 rounded-full bg-blue-500/5">
            Adım {step} / 2
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-white mb-3">Sistemi Size Özel Hazırlayalım</h1>
          <p className="text-sm text-gray-400 font-light max-w-md mx-auto leading-relaxed">
            {step === 1 
              ? 'Daha doğru analizler ve otomatik teklif taraması için iletişim ve sosyal hesaplarınızı entegre edin.' 
              : 'İlan Radarının size en uygun pozisyonları bulabilmesi için akademik ve teknik altyapınızı belirtin.'}
          </p>
        </div>

        {/* Form Container with Smooth Transition */}
        <div className="relative w-full transition-all duration-500 ease-in-out">
          
          {/* STEP 1 */}
          {step === 1 && (
            <div className="space-y-6 animate-[slideIn_0.4s_ease-out]">
              <div className="bg-[#0D121D] border border-white/[0.04] rounded-sm p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] transition-all hover:border-white/[0.08]">
                <label className="text-[11px] font-mono text-gray-400 tracking-wider uppercase mb-3 block">LinkedIn URL</label>
                <div className="relative group">
                  <Linkedin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-blue-400 transition-colors" />
                  <input
                    type="text"
                    value={formData.linkedin}
                    onChange={e => setFormData({...formData, linkedin: e.target.value})}
                    className="w-full bg-[#09090B] border border-white/[0.08] rounded-sm py-3 pl-10 pr-4 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                    placeholder="https://linkedin.com/in/profil"
                  />
                </div>
              </div>

              <div className="bg-[#0D121D] border border-white/[0.04] rounded-sm p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] transition-all hover:border-white/[0.08]">
                <label className="text-[11px] font-mono text-gray-400 tracking-wider uppercase mb-3 block">Mail Entegrasyonu (IMAP)</label>
                <div className="relative group">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-blue-400 transition-colors" />
                  <input
                    type="email"
                    value={formData.imapEmail}
                    onChange={e => setFormData({...formData, imapEmail: e.target.value})}
                    className="w-full bg-[#09090B] border border-white/[0.08] rounded-sm py-3 pl-10 pr-4 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                    placeholder="İş tekliflerini takip edeceğiniz adres"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <div className="space-y-6 animate-[slideIn_0.4s_ease-out]">
              <div className="bg-[#0D121D] border border-white/[0.04] rounded-sm p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] transition-all hover:border-white/[0.08]">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-[11px] font-mono text-gray-400 tracking-wider uppercase mb-3 block">Üniversite</label>
                    <div className="relative group">
                      <GraduationCap className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-blue-400 transition-colors pointer-events-none" />
                      <select 
                        value={formData.university}
                        onChange={e => setFormData({...formData, university: e.target.value})}
                        className="w-full bg-[#09090B] border border-white/[0.08] rounded-sm py-3 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all appearance-none cursor-pointer"
                      >
                        <option value="" disabled className="text-gray-600">Seçiniz</option>
                        {UNIVERSITIES.map(u => <option key={u} value={u}>{u}</option>)}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="text-[11px] font-mono text-gray-400 tracking-wider uppercase mb-3 block">Bölüm</label>
                    <div className="relative group">
                      <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-blue-400 transition-colors" />
                      <input
                        type="text"
                        value={formData.major}
                        onChange={e => setFormData({...formData, major: e.target.value})}
                        className="w-full bg-[#09090B] border border-white/[0.08] rounded-sm py-3 pl-10 pr-4 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                        placeholder="Örn: YBS"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-[#0D121D] border border-white/[0.04] rounded-sm p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] transition-all hover:border-white/[0.08]">
                <label className="text-[11px] font-mono text-gray-400 tracking-wider uppercase mb-4 block">İlgi Alanları (İlan Radar İçin)</label>
                <div className="flex flex-wrap gap-2">
                  {AVAILABLE_INTERESTS.map(interest => {
                    const isSelected = formData.interests.includes(interest);
                    return (
                      <button
                        key={interest}
                        onClick={() => toggleInterest(interest)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-mono transition-all duration-300 ${
                          isSelected 
                            ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-[0_0_10px_rgba(37,99,235,0.2)]' 
                            : 'bg-white/[0.02] text-gray-400 border border-white/[0.05] hover:bg-white/[0.05] hover:text-gray-300'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3" />}
                        {interest}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleNext}
            className="group w-full flex items-center justify-center gap-2 mt-8 py-4 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-sm transition-all duration-300 shadow-[0_10px_20px_-10px_rgba(37,99,235,0.4)] hover:-translate-y-1"
          >
            {step === 1 ? 'İleri' : 'Kurulumu Tamamla ve Başla'}
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
};
