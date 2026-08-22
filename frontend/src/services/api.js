const API_BASE = '/api';

/**
 * Gelişmiş Fetch Sarmalayıcısı
 */
const request = async (endpoint, options = {}) => {
  // 1. Yapılandırma ve Varsayılan Header'lar
  const config = {
    ...options,
    headers: { ...options.headers },
    // Cookie bazlı oturum (Session) kullanıyorsan aşağıdaki satırı açmalısın:
    // credentials: 'include',
  };

  // Oturum token'ı varsa her isteğe otomatik ekle
  const token = localStorage.getItem('token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  // 2. Query Parametrelerini Dinamik ve Güvenli Oluşturma
  let url = `${API_BASE}${endpoint}`;
  if (options.params) {
    // Sadece değeri olan (null/undefined olmayan) parametreleri filtrele
    const cleanParams = Object.fromEntries(
      Object.entries(options.params).filter(([_, v]) => v != null)
    );
    const query = new URLSearchParams(cleanParams).toString();
    if (query) url += `?${query}`;
  }

  // 3. JSON Body Formatlaması (FormData istisnası ile)
  if (config.body && !(config.body instanceof FormData)) {
    config.headers['Content-Type'] = 'application/json';
    config.body = JSON.stringify(config.body);
  }

  // 4. Zaman Aşımı (Timeout) Kontrolü (varsayılan 10 saniye, gerekirse override edilebilir)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeoutMs || 10000);
  config.signal = controller.signal;

  try {
    const res = await fetch(url, config);
    clearTimeout(timeoutId); // İstek başarılıysa sayacı durdur

    // Hata Yönetimi
    if (!res.ok) {
      // Oturum geçersiz/süresi dolmuş: token'ı temizle, sonraki reload'da giriş ekranına düşsün
      if (res.status === 401) {
        localStorage.removeItem('token');
      }
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.detail || errorData.message || `API Hatası: ${res.status}`;
      throw new Error(msg);
    }
    
    // 204 No Content Yönetimi
    if (res.status === 204) return null;
    
    // 5. Güvenli Response Parse (Sadece JSON ise json parse et)
    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await res.json();
    }
    
    return await res.text(); // JSON değilse düz metin veya blob dön
    
  } catch (error) {
    // Timeout hatasını özelleştirme
    if (error.name === 'AbortError') {
      console.error(`[API TIMEOUT] ${url} isteği zaman aşımına uğradı.`);
      throw new Error('Sunucu yanıt vermiyor. Lütfen bağlantınızı kontrol edin.');
    }
    
    console.error(`[API ERROR] ${url}:`, error.message);
    throw error;
  }
};

// ── Kimlik Doğrulama ──
export const login = async (email, password) => {
  const data = await request('/auth/login', { method: 'POST', body: { email, password } });
  localStorage.setItem('token', data.access_token);
  return data;
};

export const register = async (email, password, full_name) => {
  const data = await request('/auth/register', { method: 'POST', body: { email, password, full_name } });
  localStorage.setItem('token', data.access_token);
  return data;
};

export const loginWithGoogle = async (code) => {
  const data = await request('/auth/google', { method: 'POST', body: { code } });
  localStorage.setItem('token', data.access_token);
  return data;
};

export const logout = async () => {
  // Sunucu tarafında token_version'ı artırıp bu andan önceki tüm JWT'leri
  // (tüm cihazlar dahil) geçersiz kılar. Ağ hatası olsa bile kullanıcı yerel
  // olarak çıkış yapabilsin diye hata yutuluyor.
  try {
    await request('/auth/logout', { method: 'POST' });
  } catch {
    // yut
  } finally {
    localStorage.removeItem('token');
  }
};

export const getToken = () => localStorage.getItem('token');

// ── GET Istekleri ──
export const getJobs = () => request('/jobs/');
export const getInboxItems = () => request('/inbox/items');
export const getCVs = () => request('/cvs/');
export const getProfile = () => request('/users/profile');
export const getAccounts = () => request('/inbox/accounts');
export const getEvents = () => request('/events/');
export const updateEventStatus = (event_id, status) => request(`/events/${event_id}/status`, {
  method: 'PATCH',
  body: { status },
});
export const getDashboardStats = () => request('/dashboard/stats');

// Artık params objesi kullanıyoruz. status undefined ise URL bozulmaz.
export const getApplications = (status) => request('/applications/', { 
  params: { status } 
});

// ── POST Istekleri ──
// syncJobs artık { task_id, status } döndürüyor — useTaskStream ile SSE takibi yap
export const syncJobs = () => request('/jobs/sync', { method: 'POST' });
export const syncInbox = () => request('/inbox/sync', { method: 'POST' });
export const markInboxItemRead = (item_id) => request(`/inbox/items/${item_id}/read`, { method: 'PATCH' });
export const convertInboxItemToJob = (item_id) => request(`/inbox/items/${item_id}/convert-to-job`, { method: 'POST' });
export const linkEmailAccount = (email, app_password) => request('/inbox/accounts', {
  method: 'POST',
  body: { email, app_password }
});
export const prepareOutreach = (company_name) => request('/outreach/prepare', {
  method: 'POST',
  body: { company_name }
});
export const sendOutreach = (outreach_id, target_email = null) => request(`/outreach/${outreach_id}/send`, {
  method: 'POST',
  body: { target_email }
});

// ── Job işlemleri ──
export const matchJob = (job_id, cv_id = null) => request(`/jobs/${job_id}/match`, {
  method: 'POST',
  params: cv_id ? { cv_id } : {},
});
export const toggleFavorite = (job_id) => request(`/jobs/${job_id}/favorite`, { method: 'PATCH' });
export const updateJobStatus = (job_id, status) => request(`/jobs/${job_id}/status`, {
  method: 'PATCH',
  body: { status },
});

// ── CV işlemleri ──
export const triggerAtsAnalysis = (cv_id) => request(`/cvs/${cv_id}/ats-analyze`, { method: 'POST' });
export const generateCv = (data) => request('/cvs/generate', { method: 'POST', body: data });

// ── PATCH Istekleri ──
export const updateProfile = (data) => request('/users/profile', {
  method: 'PATCH',
  body: data
});
export const approveApplication = (app_id, approved, notes = null, contact_email = null) => request(`/applications/${app_id}/approve`, {
  method: 'POST', // Backend POST bekliyorsa burada POST kalmalı, ancak genelde approve işlemleri PATCH olur
  body: { approved, notes, contact_email }
});

// ── FormData Istekleri ──
export const uploadCV = (file, title, variant) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('variant_type', variant);
  
  return request('/cvs/upload', { 
    method: 'POST', 
    body: formData 
  });
};

// ── Detay Istekleri ──
export const getJobDetail = (id) => request(`/jobs/${id}`);
export const getCVDetail = (id) => request(`/cvs/${id}`);

// ── CV Varsayılan Ayarla ──
export const setDefaultCV = (id) => request(`/cvs/${id}/set-default`, { method: 'PATCH' });

// ── Başvuru Hazırla ── (mektup + soru-cevap + e-posta keşfi paralel 3 AI çağrısı
// yapıyor; geçici Gemini yoğunluğunda backend'in kendi retry'ı bile 10sn'yi
// aşabiliyor, o yüzden burada daha geniş bir zaman aşımı kullanıyoruz.)
export const prepareApplication = (job_id, cv_id = null) => request('/applications/prepare', {
  method: 'POST',
  body: { job_id, cv_id },
  timeoutMs: 45000,
});

// ── Başvuru Gönder (onaylanmış başvuruyu gönderime çevir) ──
export const submitApplication = (app_id) => request(`/applications/${app_id}/submit`, {
  method: 'POST',
});

// ── İlana Özel Soruları Cevapla (kullanıcı formdaki gerçek soruları yapıştırır) ──
export const answerCustomQuestions = (app_id, questions) => request(`/applications/${app_id}/answer-questions`, {
  method: 'POST',
  body: { questions },
  timeoutMs: 30000,
});

// ── Mezun/Referans Bulucu (Google Search grounding ile Gemini) ──
export const findReferrals = (app_id) => request(`/applications/${app_id}/find-referrals`, {
  method: 'POST',
  timeoutMs: 30000,
});

// ── Ön Yazıyı Sohbet Tarzı Düzenle ──
export const reviseCoverLetter = (app_id, instruction) => request(`/applications/${app_id}/revise-cover-letter`, {
  method: 'POST',
  body: { instruction },
  timeoutMs: 30000,
});

// ── Başvuru Sonrası Takip ──
export const draftFollowup = (app_id) => request(`/applications/${app_id}/draft-followup`, {
  method: 'POST',
  timeoutMs: 30000,
});
export const sendFollowup = (app_id, body) => request(`/applications/${app_id}/send-followup`, {
  method: 'POST',
  body: { body },
});
export const markResponded = (app_id) => request(`/applications/${app_id}/mark-responded`, {
  method: 'POST',
});

// ── Gerçek Sonuç Takibi (mülakat/teklif/red) ──
export const updateApplicationOutcome = (app_id, outcome) => request(`/applications/${app_id}/outcome`, {
  method: 'PATCH',
  body: { outcome },
});

// ── DELETE Istekleri ──
export const deleteCV = (id) => request(`/cvs/${id}`, { method: 'DELETE' });