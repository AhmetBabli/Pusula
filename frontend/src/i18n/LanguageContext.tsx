import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Language = 'tr' | 'en';

interface Translations {
  [key: string]: {
    [key in Language]: string;
  };
}

const LANGUAGE_STORAGE_KEY = 'language';

const translations: Translations = {
  // ── Navigation ──
  nav_dashboard: { tr: 'Yönetim Paneli', en: 'Dashboard' },
  nav_market_analysis: { tr: 'Fırsatlar', en: 'Opportunities' },
  nav_applications: { tr: 'Başvurular', en: 'Applications' },
  nav_events: { tr: 'Etkinlikler', en: 'Events' },
  nav_portfolio: { tr: 'Portföy', en: 'Portfolio' },
  nav_inbox: { tr: 'Gelen Kutusu', en: 'Inbox' },
  nav_agents: { tr: 'Otomasyon', en: 'Automation' },
  nav_home: { tr: 'Ana Sayfa', en: 'Home' },
  nav_menu_label: { tr: 'Sistem Menüsü', en: 'System Menu' },
  nav_go_to_suffix: { tr: 'sekmesine geç', en: '' },

  // ── Header ──
  app_title: { tr: 'Kariyer Ajanı', en: 'Career Agent' },
  app_subtitle: { tr: 'Kariyer Otomasyon Platformu', en: 'Career Automation Platform' },
  my_profile: { tr: 'Profilim', en: 'My Profile' },
  admin: { tr: 'Yönetici', en: 'Admin' },
  header_open_menu: { tr: 'Menüyü Aç', en: 'Open Menu' },
  header_close_menu: { tr: 'Menüyü Kapat', en: 'Close Menu' },
  header_light_theme: { tr: 'Açık temaya geç', en: 'Switch to light theme' },
  header_dark_theme: { tr: 'Koyu temaya geç', en: 'Switch to dark theme' },

  // ── Dashboard (Genel Bakış) ──
  dashboard_title: { tr: 'Genel Bakış', en: 'Overview' },
  dashboard_subtitle: { tr: 'Başvuru sürecinizin güncel özeti.', en: 'A current summary of your application process.' },
  dashboard_stat_total_jobs: { tr: 'TOPLAM İLAN', en: 'TOTAL JOBS' },
  dashboard_stat_new_jobs: { tr: 'YENİ İLAN', en: 'NEW JOBS' },
  dashboard_stat_applications: { tr: 'BAŞVURULAR', en: 'APPLICATIONS' },
  dashboard_stat_pending: { tr: 'BEKLEYEN ONAY', en: 'PENDING APPROVAL' },
  dashboard_scan_jobs: { tr: 'İLAN TARA', en: 'SCAN JOBS' },
  dashboard_scanning: { tr: 'TARANIYOR...', en: 'SCANNING...' },
  dashboard_scan_inbox: { tr: 'GELEN KUTUSUNU TARA', en: 'SCAN INBOX' },
  dashboard_connect_gmail: { tr: 'GMAIL BAĞLA', en: 'CONNECT GMAIL' },
  dashboard_cold_email: { tr: 'SOĞUK E-POSTA', en: 'COLD EMAIL' },
  dashboard_top_matches: { tr: 'EN İYİ EŞLEŞMELER', en: 'TOP MATCHES' },
  dashboard_see_all: { tr: 'Tümünü Gör', en: 'See All' },

  // ── Jobs (Fırsatlar) ──
  jobs_title: { tr: 'Fırsatlar', en: 'Opportunities' },
  jobs_active_suffix: { tr: 'Aktif İlan // Derin Tarama Hazır', en: 'Active Listings // Deep Scan Ready' },
  jobs_search_placeholder: { tr: 'İlan veya şirket ara...', en: 'Search jobs or companies...' },
  jobs_all_sources: { tr: 'Tüm Kaynaklar', en: 'All Sources' },
  jobs_all_statuses: { tr: 'Tüm Durumlar', en: 'All Statuses' },
  jobs_sort_match: { tr: 'Eşleşme Skoru', en: 'Match Score' },
  jobs_sort_date: { tr: 'Son Tarih', en: 'Deadline' },
  jobs_sort_company: { tr: 'Şirket', en: 'Company' },
  jobs_empty_title: { tr: 'İlan bulunamadı.', en: 'No listings found.' },
  jobs_empty_desc: { tr: 'Farklı arama kriterleri deneyin veya derin tarama başlatın.', en: 'Try different search criteria or start a deep scan.' },
  jobs_badge_new: { tr: 'Yeni', en: 'New' },
  jobs_detail_button: { tr: 'Detay', en: 'Details' },
  jobs_detail_title_fallback: { tr: 'İLAN DETAYI', en: 'JOB DETAILS' },
  jobs_description: { tr: 'Açıklama', en: 'Description' },
  jobs_requirements: { tr: 'Gereksinimler', en: 'Requirements' },
  jobs_ai_evaluation: { tr: 'AI Değerlendirmesi', en: 'AI Evaluation' },
  jobs_prepare_application: { tr: 'BAŞVURU HAZIRLA', en: 'PREPARE APPLICATION' },
  jobs_go_to_listing: { tr: 'İLANA GİT', en: 'VIEW LISTING' },
  jobs_type_staj: { tr: 'Staj', en: 'Internship' },
  jobs_type_tam_zamanli: { tr: 'Tam Zamanlı', en: 'Full-time' },
  jobs_type_is: { tr: 'İş', en: 'Job' },

  // ── Applications (Başvurular) ──
  applications_title: { tr: 'Başvuru Takip', en: 'Application Tracking' },
  applications_count_suffix: { tr: 'Başvuru // İş Akışı', en: 'Applications // Workflow' },
  applications_filter_all: { tr: 'Tümü', en: 'All' },
  applications_status_draft: { tr: 'TASLAK', en: 'DRAFT' },
  applications_status_awaiting: { tr: 'ONAY BEKLİYOR', en: 'AWAITING APPROVAL' },
  applications_status_approved: { tr: 'ONAYLANDI', en: 'APPROVED' },
  applications_status_submitted: { tr: 'GÖNDERİLDİ', en: 'SUBMITTED' },
  applications_empty_title: { tr: 'Henüz başvuru yok', en: 'No applications yet' },
  applications_empty_desc: { tr: 'İş ilanlarından başvuru hazırlayarak başlayın.', en: 'Get started by preparing an application from a job listing.' },
  applications_untitled_job: { tr: 'İsimsiz İlan', en: 'Untitled Listing' },
  applications_approve: { tr: 'Onayla', en: 'Approve' },
  applications_reject: { tr: 'Reddet', en: 'Reject' },
  applications_send: { tr: 'GÖNDER', en: 'SEND' },
  applications_retry: { tr: 'TEKRAR DENE', en: 'RETRY' },
  applications_contact_email_label: { tr: 'Başvuru E-postası', en: 'Application Email' },
  applications_contact_email_placeholder: { tr: 'Bu ilan için e-posta bulunamadı — onaylarsan kopyala-yapıştır paketi hazırlanacak', en: 'No email found for this listing — approving will prepare a copy-paste package' },
  applications_source_job_posting: { tr: 'İlan içinden bulundu', en: 'Found in the job listing' },
  applications_source_web_search: { tr: "Web'de tahmin edildi — göndermeden önce kontrol edin", en: 'Guessed via web search — verify before sending' },
  applications_source_manual: { tr: 'Elle girildi', en: 'Entered manually' },
  applications_will_send_to: { tr: 'Gönderilecek adres:', en: 'Will send to:' },
  applications_no_email_hint: { tr: 'E-posta bulunamadı — gönderince kopyala-yapıştır paketi hazırlanacak', en: 'No email found — sending will prepare a copy-paste package' },
  applications_send_failed_fallback: { tr: 'Gönderim başarısız oldu.', en: 'Sending failed.' },
  applications_manual_fallback_desc: { tr: 'Bu ilan için otomatik gönderim yapılamadı — CV ve ön yazıyı kopyalayıp ilana giderek elle başvurun.', en: 'Automatic sending was not possible for this listing — copy the CV and cover letter and apply manually via the listing.' },
  applications_go_to_listing: { tr: 'İlana Git', en: 'View Listing' },

  // ── Events (Etkinlikler) ──
  events_title: { tr: 'Etkinlikler', en: 'Events' },
  events_upcoming_suffix: { tr: 'Yaklaşan Etkinlik // Kariyer Takvimi', en: 'Upcoming Events // Career Calendar' },
  events_empty_title: { tr: 'Henüz etkinlik bulunmuyor.', en: 'No events yet.' },
  events_empty_desc: { tr: 'Yaklaşan kariyer fuarları ve etkinlikler burada listelenecek.', en: 'Upcoming career fairs and events will be listed here.' },
  events_details_link: { tr: 'Etkinlik Detayları', en: 'Event Details' },

  // ── CV (Portföy) ──
  cv_title: { tr: 'Portföy', en: 'Portfolio' },
  cv_ats_active_suffix: { tr: 'CV // ATS Analizi Aktif', en: 'CVs // ATS Analysis Active' },
  cv_new_button: { tr: 'YENİ CV', en: 'NEW CV' },
  cv_empty_title: { tr: 'Henüz CV yüklenmemiş', en: 'No CV uploaded yet' },
  cv_empty_desc: { tr: 'Kariyer fırsatlarını değerlendirmek için bir CV yükleyin. AI analizi anında başlayacaktır.', en: 'Upload a CV to start evaluating career opportunities. AI analysis will begin instantly.' },
  cv_default_badge: { tr: 'Varsayılan', en: 'Default' },
  cv_ai_generated_badge: { tr: 'AI Tarafından Oluşturuldu', en: 'AI Generated' },
  cv_pdf: { tr: 'PDF', en: 'PDF' },
  cv_text: { tr: 'METİN', en: 'TEXT' },
  cv_detail_button: { tr: 'Detay', en: 'Details' },
  cv_detail_title_fallback: { tr: 'CV DETAYI', en: 'CV DETAILS' },
  cv_ats_score: { tr: 'ATS Skoru', en: 'ATS Score' },
  cv_ai_feedback: { tr: 'AI Geri Bildirimi', en: 'AI Feedback' },
  cv_strengths: { tr: 'Güçlü Yönler', en: 'Strengths' },
  cv_weaknesses: { tr: 'İyileştirme Alanları', en: 'Areas for Improvement' },
  cv_content: { tr: 'CV İçeriği', en: 'CV Content' },
  cv_set_default: { tr: 'VARSAYILAN YAP', en: 'SET AS DEFAULT' },
  cv_delete: { tr: 'SİL', en: 'DELETE' },
  cv_upload_title: { tr: 'YENİ CV YÜKLE', en: 'UPLOAD NEW CV' },
  cv_upload_desc: { tr: 'PDF formatındaki özgeçmişinizi sisteme entegre edin. AI otomatik analiz yapacak.', en: 'Integrate your PDF resume into the system. AI will analyze it automatically.' },
  cv_variant_general: { tr: 'Genel Özgeçmiş', en: 'General Resume' },
  cv_variant_ai: { tr: 'Yapay Zeka Odaklı', en: 'AI-Focused' },
  cv_variant_cyber: { tr: 'Siber Güvenlik Odaklı', en: 'Cybersecurity-Focused' },
  cv_variant_it: { tr: 'IT & Sistem Yönetimi', en: 'IT & Systems Administration' },
  cv_analyzing: { tr: 'ANALİZ YAPILIYOR...', en: 'ANALYZING...' },
  cv_upload_and_analyze: { tr: 'YÜKLE VE ANALİZ ET', en: 'UPLOAD AND ANALYZE' },

  // ── Inbox (Gelen Kutusu) ──
  inbox_title: { tr: 'Gelen Kutusu', en: 'Inbox' },
  inbox_opportunities_suffix: { tr: 'Kariyer Fırsatı // AI İstihbarat', en: 'Career Opportunities // AI Intelligence' },
  inbox_syncing: { tr: 'Senkronize Ediliyor...', en: 'Syncing...' },
  inbox_sync: { tr: 'Senkronize Et', en: 'Sync' },
  inbox_empty_title: { tr: 'Henüz kariyer fırsatı bulunamadı.', en: 'No career opportunities found yet.' },
  inbox_empty_desc: { tr: 'Gmail hesabınızı bağlayarak e-postalarınızı tarayın.', en: 'Connect your Gmail account to scan your emails.' },
  inbox_type_job: { tr: 'İŞ İLANI', en: 'JOB LISTING' },
  inbox_type_event: { tr: 'ETKİNLİK', en: 'EVENT' },
  inbox_type_hackathon: { tr: 'HACKATHON', en: 'HACKATHON' },
  inbox_type_career_fair: { tr: 'KARİYER FUARI', en: 'CAREER FAIR' },
  inbox_type_course: { tr: 'EĞİTİM', en: 'COURSE' },
  inbox_type_update: { tr: 'GÜNCELLEME', en: 'UPDATE' },

  // ── AI Asistanları (Otomasyon) ──
  agents_title: { tr: 'AI Asistanları', en: 'AI Assistants' },
  agents_subtitle: { tr: "CV'nizi geliştirmek, iş fırsatlarını araştırmak ve iletişim taslakları hazırlamak için AI asistanlarını kullanın.", en: 'Use AI assistants to improve your CV, research job opportunities, and prepare outreach drafts.' },
  agents_connected: { tr: 'Bağlı', en: 'Connected' },
  agents_disconnected: { tr: 'Bağlantı Yok', en: 'Disconnected' },
  agents_reset_title: { tr: 'Sıfırla', en: 'Reset' },
  agents_status_running: { tr: 'Çalışıyor', en: 'Running' },
  agents_status_complete: { tr: 'Tamamlandı', en: 'Complete' },
  agents_status_failed: { tr: 'Başarısız', en: 'Failed' },
  agents_research_title: { tr: 'Araştırma Asistanı', en: 'Research Assistant' },
  agents_research_subtitle: { tr: 'İş ilanı ve şirket araştırması', en: 'Job and company research' },
  agents_search_query_placeholder: { tr: 'Arama (örn. React Developer)', en: 'Search (e.g. React Developer)' },
  agents_location_placeholder: { tr: 'Konum', en: 'Location' },
  agents_search_button: { tr: 'Ara', en: 'Search' },
  agents_jobs_found_suffix: { tr: 'yeni iş ilanı bulundu ve kaydedildi.', en: 'new job listings found and saved.' },
  agents_review_in: { tr: 'sekmesinden inceleyebilirsiniz.', en: 'You can review them in the' },
  agents_cv_title: { tr: 'CV Oluşturucu', en: 'CV Builder' },
  agents_cv_subtitle: { tr: 'GitHub profilinizden otomatik CV oluşturur', en: 'Automatically builds a CV from your GitHub profile' },
  agents_cv_start_button: { tr: 'CV Oluşturmayı Başlat', en: 'Start Building CV' },
  agents_cv_download: { tr: 'PDF Olarak İndir', en: 'Download as PDF' },
  agents_interview_title: { tr: 'Mülakat Koçu', en: 'Interview Coach' },
  agents_interview_subtitle: { tr: 'Hedefe özel mülakat simülasyonu', en: 'Targeted interview simulation' },
  agents_interview_open: { tr: 'Simülatörü Aç', en: 'Open Simulator' },
  agents_outreach_title: { tr: 'İletişim Asistanı', en: 'Outreach Assistant' },
  agents_outreach_subtitle: { tr: 'Soğuk e-posta ve LinkedIn mesajı hazırlar', en: 'Prepares cold emails and LinkedIn messages' },
  agents_outreach_company_placeholder: { tr: 'Hedef Şirket Adı...', en: 'Target Company Name...' },
  agents_outreach_generate: { tr: 'Oluştur', en: 'Generate' },
  agents_outreach_email_draft: { tr: 'Soğuk E-posta Taslağı', en: 'Cold Email Draft' },
  agents_outreach_linkedin_draft: { tr: 'LinkedIn Mesaj Taslağı', en: 'LinkedIn Message Draft' },
  agents_log_hide: { tr: 'İşlem Kaydını Gizle', en: 'Hide Activity Log' },
  agents_log_show: { tr: 'İşlem Kaydını Göster', en: 'Show Activity Log' },
  agents_log_entries_suffix: { tr: 'kayıt', en: 'entries' },
  agents_log_empty: { tr: 'Henüz işlem kaydı yok.', en: 'No activity logged yet.' },

  // ── Mülakat Koçu (InterviewCoach) ──
  interview_setup_title: { tr: 'Mülakat Simülatörü', en: 'Interview Simulator' },
  interview_setup_subtitle: { tr: 'Hedefe özel pratik oturumunuzu ayarlayın.', en: 'Set up your targeted practice session.' },
  interview_target_company: { tr: 'Hedef Şirket', en: 'Target Company' },
  interview_target_company_placeholder: { tr: 'Örn. Turkcell, Baykar, Getir...', en: 'e.g. Google, Amazon, Stripe...' },
  interview_target_position: { tr: 'Hedef Pozisyon', en: 'Target Position' },
  interview_target_position_placeholder: { tr: 'Örn. Kıdemli Frontend Geliştirici...', en: 'e.g. Senior Frontend Engineer...' },
  interview_type_label: { tr: 'Mülakat Türü', en: 'Interview Type' },
  interview_type_technical: { tr: 'Teknik', en: 'Technical' },
  interview_type_hr: { tr: 'İK / Kültürel', en: 'HR / Cultural' },
  interview_type_mixed: { tr: 'Karma', en: 'Mixed' },
  interview_preparing: { tr: 'Sorular Hazırlanıyor...', en: 'Preparing Questions...' },
  interview_start: { tr: 'Simülasyonu Başlat', en: 'Start Simulation' },
  interview_results_title: { tr: 'Performans Analizi', en: 'Performance Analysis' },
  interview_results_subtitle: { tr: 'Mülakat simülasyonunuzun detaylı değerlendirmesi.', en: 'A detailed evaluation of your interview simulation.' },
  interview_average_score: { tr: 'Ortalama Puan', en: 'Average Score' },
  interview_summary_verdict: { tr: 'Genel Değerlendirme', en: 'Overall Assessment' },
  interview_verdict_strong: { tr: 'Güçlü bir performans. Net bir iletişim ve sağlam alan bilgisi gösterdiniz. Bu pozisyon için iyi hazırlanmışsınız.', en: 'Strong performance. You demonstrated clear communication and solid domain knowledge. You are well prepared for this role.' },
  interview_verdict_moderate: { tr: 'Orta düzey bir performans. Temeliniz sağlam ama yanıtlarınız daha fazla yapı (örn. STAR yöntemi) ve derinlik gerektiriyor.', en: 'Moderate performance. While your foundation is solid, your answers need more structure (e.g. the STAR method) and depth.' },
  interview_verdict_needs_work: { tr: 'Geliştirilmesi gereken alanlar var. Gerçek mülakata girmeden önce temel kavramları iyice anlamaya ve yanıtlarınızı net bir şekilde yapılandırmaya odaklanın.', en: 'Needs improvement. Focus on thoroughly understanding core concepts and clearly structuring your answers before the real interview.' },
  interview_question_breakdown: { tr: 'Soru Bazlı Değerlendirme', en: 'Question Breakdown' },
  interview_outreach_title: { tr: 'Soğuk İletişim Asistanı', en: 'Cold Outreach Assistant' },
  interview_outreach_desc: { tr: 'İşe alım uzmanına ulaşmak için özel bir LinkedIn/E-posta taslağı oluşturun.', en: 'Generate a tailored LinkedIn/Email draft to reach out to the recruiter.' },
  interview_outreach_generating: { tr: 'Oluşturuluyor...', en: 'Generating...' },
  interview_outreach_generate_draft: { tr: 'Taslak Oluştur', en: 'Generate Draft' },
  interview_outreach_cold_email: { tr: 'Soğuk E-posta', en: 'Cold Email' },
  interview_outreach_linkedin_dm: { tr: 'LinkedIn Mesajı', en: 'LinkedIn Message' },
  interview_new_simulation: { tr: 'Yeni Simülasyon Başlat', en: 'Start New Simulation' },
  interview_question_progress: { tr: 'Soru', en: 'Question' },
  interview_technical_badge: { tr: 'TEKNİK', en: 'TECHNICAL' },
  interview_cultural_badge: { tr: 'KÜLTÜREL', en: 'CULTURAL' },
  interview_answer_placeholder: { tr: 'Yanıtınızı buraya yazın. Davranışsal sorular için STAR yöntemini (Durum, Görev, Aksiyon, Sonuç) kullanmayı deneyin...', en: 'Type your response here. Try using the STAR method (Situation, Task, Action, Result) for behavioral questions...' },
  interview_analyzing: { tr: 'Yanıt Analiz Ediliyor...', en: 'Analyzing Response...' },
  interview_submit_answer: { tr: 'Yanıtı Gönder', en: 'Submit Answer' },
  interview_evaluation: { tr: 'Değerlendirme', en: 'Evaluation' },
  interview_view_results: { tr: 'Sonuçları Gör', en: 'View Final Results' },
  interview_next_question: { tr: 'Sonraki Soru', en: 'Next Question' },

  // ── Profil (ProfileView) ──
  profile_title: { tr: 'Profil Ayarları', en: 'Profile Settings' },
  profile_subtitle: { tr: 'Hesap kimliğini ve kariyer tercihlerini yönet.', en: 'Manage your account identity and career preferences.' },
  profile_logout: { tr: 'Çıkış Yap', en: 'Log Out' },
  profile_identity_title: { tr: 'Kimlik ve Akademik Bilgiler', en: 'Identity and Academic Information' },
  profile_identity_desc: { tr: 'Bu bilgiler ön yazı ve mülakat hazırlığında AI tarafından kullanılır.', en: 'This information is used by AI when preparing cover letters and interviews.' },
  profile_full_name: { tr: 'Ad Soyad', en: 'Full Name' },
  profile_email: { tr: 'E-Posta', en: 'Email' },
  profile_university: { tr: 'Üniversite', en: 'University' },
  profile_department: { tr: 'Bölüm', en: 'Department' },
  profile_graduation_year: { tr: 'Mezuniyet Yılı', en: 'Graduation Year' },
  profile_skills_title: { tr: 'Yetenekler', en: 'Skills' },
  profile_skills_desc: { tr: 'İlan eşleştirme ve CV üretimi bu becerilere göre yapılır.', en: 'Job matching and CV generation are based on these skills.' },
  profile_skill_placeholder: { tr: "Bir yetenek yazıp Enter'a basın...", en: 'Type a skill and press Enter...' },
  profile_sectors_title: { tr: 'Hedef Sektörler', en: 'Target Sectors' },
  profile_sectors_desc: { tr: 'İlan taraması bu sektörlere öncelik verir.', en: 'Job scanning prioritizes these sectors.' },
  profile_sector_placeholder: { tr: "Bir sektör yazıp Enter'a basın...", en: 'Type a sector and press Enter...' },
  profile_languages_title: { tr: 'Diller', en: 'Languages' },
  profile_languages_desc: { tr: 'Konuştuğunuz diller ön yazılarda belirtilir.', en: 'Languages you speak are mentioned in cover letters.' },
  profile_language_placeholder: { tr: "Bir dil yazıp Enter'a basın...", en: 'Type a language and press Enter...' },
  profile_links_title: { tr: 'Bağlantılar ve Özet', en: 'Links and Summary' },
  profile_links_desc: { tr: 'Ön yazılarda ve mülakat hazırlığında kullanılacak kısa tanıtım.', en: 'A short bio used in cover letters and interview prep.' },
  profile_summary: { tr: 'Kısa Özet', en: 'Short Summary' },
  profile_discard: { tr: 'Değişiklikleri Geri Al', en: 'Discard Changes' },
  profile_save: { tr: 'Profili Kaydet', en: 'Save Profile' },
  profile_saving: { tr: 'Kaydediliyor...', en: 'Saving...' },
  profile_saved: { tr: 'Kaydedildi!', en: 'Saved!' },
  profile_save_error: { tr: 'Profil kaydedilemedi.', en: 'Profile could not be saved.' },

  // ── Gmail Modal ──
  gmail_modal_title: { tr: 'GMAIL AJAN YETKİLENDİRME', en: 'GMAIL AGENT AUTHORIZATION' },
  gmail_modal_info: { tr: 'Gmail hesabınızı bağlamak için "Uygulama Şifresi" kullanmalısınız.', en: 'You must use an "App Password" to connect your Gmail account.' },
  gmail_modal_info_path: { tr: 'Google Hesabı > Güvenlik > 2 Adımlı Doğrulama > Uygulama Şifreleri', en: 'Google Account > Security > 2-Step Verification > App Passwords' },
  gmail_modal_email_placeholder: { tr: 'Gmail Adresiniz', en: 'Your Gmail Address' },
  gmail_modal_password_placeholder: { tr: 'Uygulama Şifresi (16 Haneli)', en: 'App Password (16 characters)' },
  gmail_modal_connecting: { tr: 'BAĞLANIYOR...', en: 'CONNECTING...' },
  gmail_modal_connect: { tr: 'HESABI BAĞLA', en: 'CONNECT ACCOUNT' },

  // ── Outreach Modal ──
  outreach_modal_title: { tr: 'SOĞUK BAŞVURU', en: 'COLD APPLICATION' },
  outreach_modal_info: { tr: 'Hedef şirketin İK e-posta adresini otomatik bulur, AI ile özel önyazı hazırlar ve gönderir.', en: "Automatically finds the target company's HR email, prepares a tailored cover letter with AI, and sends it." },
  outreach_modal_company_label: { tr: 'Şirket Adı', en: 'Company Name' },
  outreach_modal_company_placeholder: { tr: 'Örn: Baykar, Turkcell, Garanti BBVA...', en: 'e.g. Google, Amazon, Microsoft...' },
  outreach_modal_sending: { tr: 'GÖNDERİLİYOR...', en: 'SENDING...' },
  outreach_modal_send: { tr: 'SOĞUK E-POSTA GÖNDER', en: 'SEND COLD EMAIL' },

  // ── Auth ──
  auth_subtitle: { tr: 'Kurumsal Hesap Girişi', en: 'Enterprise Account Login' },
  auth_login_tab: { tr: 'Giriş Yap', en: 'Log In' },
  auth_register_tab: { tr: 'Üye Ol', en: 'Sign Up' },
  auth_full_name: { tr: 'Ad Soyad', en: 'Full Name' },
  auth_full_name_placeholder: { tr: 'Adınız Soyadınız', en: 'Your Full Name' },
  auth_email: { tr: 'E-Posta', en: 'Email' },
  auth_email_placeholder: { tr: 'ornek@sirket.com', en: 'example@company.com' },
  auth_password: { tr: 'Şifre', en: 'Password' },
  auth_waiting: { tr: 'Bekleyin...', en: 'Please wait...' },
  auth_login_submit: { tr: 'Sisteme Giriş Yap', en: 'Log In to System' },
  auth_register_submit: { tr: 'Kayıt Ol ve Devam Et', en: 'Sign Up and Continue' },
  auth_generic_error: { tr: 'Bir hata oluştu. Lütfen tekrar deneyin.', en: 'An error occurred. Please try again.' },
  auth_google_button: { tr: 'Google ile Bağlan', en: 'Continue with Google' },
  auth_google_connecting: { tr: 'Google\'a bağlanılıyor...', en: 'Connecting to Google...' },
  auth_google_note: { tr: 'İpucu: Başvuru e-postalarınızı göndermek istediğiniz Gmail hesabıyla kayıt olun — bağlandığınızda sistem doğrudan o hesaptan gönderim yapabilir.', en: 'Tip: Sign up with the Gmail account you want to send applications from — once connected, the system can send directly from that account.' },
  auth_google_error: { tr: 'Google ile bağlantı başarısız oldu. Lütfen tekrar deneyin.', en: 'Google sign-in failed. Please try again.' },
  auth_google_not_configured: { tr: 'Google girişi bu sunucuda henüz yapılandırılmadı.', en: 'Google sign-in is not configured on this server yet.' },
  auth_divider_or: { tr: 'veya', en: 'or' },

  // ── Onboarding (pazarlama ekranı) ──
  onboarding_how_it_works: { tr: 'Nasıl Çalışır', en: 'How It Works' },
  onboarding_heading_1: { tr: 'Kariyer Sürecinizi', en: 'Manage Your Career' },
  onboarding_heading_2: { tr: 'Yapay Zeka ile Yönetin.', en: 'Journey With AI.' },
  onboarding_intro: { tr: 'Kariyer Ajanı; veri odaklı analizler, başvuru hazırlığı ve mülakat provalarıyla profesyonel gelişiminizi tek platformdan yönetmenizi sağlar.', en: 'Career Agent lets you manage your professional growth from a single platform — with data-driven analysis, application preparation, and interview rehearsal.' },
  onboarding_feature_cv_title: { tr: "ATS Uyumlu CV'ler", en: 'ATS-Compliant CVs' },
  onboarding_feature_cv_desc: { tr: 'Kurumsal başvuru takip sistemlerinden geçebilen, algoritma dostu özgeçmişler oluşturur.', en: 'Generates algorithm-friendly resumes that pass enterprise applicant tracking systems.' },
  onboarding_feature_radar_title: { tr: 'Otomatik İlan Takibi', en: 'Automatic Job Tracking' },
  onboarding_feature_radar_desc: { tr: 'Yerel ve küresel iş piyasasını sürekli tarayarak yetkinliklerinize uygun ilanları bulur.', en: 'Continuously scans local and global job markets to find listings matching your skills.' },
  onboarding_feature_inbox_title: { tr: 'Akıllı Gelen Kutusu', en: 'Smart Inbox' },
  onboarding_feature_inbox_desc: { tr: 'Gelen iş teklifi ve mülakat davetlerini yapay zeka ile otomatik sınıflandırır.', en: 'Automatically classifies incoming job offers and interview invitations with AI.' },
  onboarding_start_button: { tr: 'Başlayalım', en: "Let's Start" },

  // ── Feature Tour (kayıt sonrası bölüm tanıtımı) ──
  tour_section_1_title: { tr: 'Genel Bakış', en: 'Overview' },
  tour_section_1_desc: { tr: 'Başvuru sürecinizin özeti burada. Toplam ilan, yeni ilan ve bekleyen onay sayısını görür; tek tıkla ilan tarama veya gelen kutusu senkronizasyonu başlatabilirsiniz.', en: 'A summary of your application process. See total jobs, new jobs, and pending approvals; start a job scan or inbox sync with one click.' },
  tour_section_2_title: { tr: 'Fırsatlar', en: 'Opportunities' },
  tour_section_2_desc: { tr: 'Taranan tüm iş ve staj ilanları burada listelenir. Her ilan için AI eşleşme skorunu görür, filtreleyip arayabilir, uygun bulduğunuz ilan için başvuru hazırlatabilirsiniz.', en: 'All scanned job and internship listings are shown here. See the AI match score for each, filter and search, and prepare an application for any listing you like.' },
  tour_section_3_title: { tr: 'Başvurular', en: 'Applications' },
  tour_section_3_desc: { tr: 'Hazırlanan her başvuru burada takip edilir: taslak → onay bekliyor → onaylandı → gönderildi.', en: 'Every prepared application is tracked here: draft → awaiting approval → approved → submitted.' },
  tour_section_3_highlight: { tr: 'Önemli: hiçbir başvuru veya e-posta sizin onayınız olmadan gönderilmez — sistem sadece hazırlar, kararı siz verirsiniz.', en: 'Important: no application or email is ever sent without your approval — the system only prepares, you decide.' },
  tour_section_4_title: { tr: 'Etkinlikler', en: 'Events' },
  tour_section_4_desc: { tr: 'Kariyer fuarları, hackathonlar ve networking etkinlikleri burada listelenir.', en: 'Career fairs, hackathons, and networking events are listed here.' },
  tour_section_5_title: { tr: 'Portföy', en: 'Portfolio' },
  tour_section_5_desc: { tr: "CV'lerinizi buradan yükler, yapay zekanın ATS uyumluluk analizini görürsünüz. Başvurularda kullanılacak varsayılan CV'nizi de burada belirlersiniz.", en: "Upload your CVs here and see the AI's ATS compatibility analysis. Also set the default CV to be used for applications." },
  tour_section_6_title: { tr: 'Gelen Kutusu', en: 'Inbox' },
  tour_section_6_desc: { tr: 'Gmail hesabınızı bağlayarak gelen iş teklifi ve mülakat davetlerinin otomatik olarak yakalanmasını sağlayabilirsiniz.', en: 'Connect your Gmail account to automatically capture incoming job offers and interview invitations.' },
  tour_section_7_title: { tr: 'Otomasyon', en: 'Automation' },
  tour_section_7_desc: { tr: 'AI asistanları: iş ve şirket araştırması, otomatik CV oluşturma, mülakat pratiği ve iletişim taslakları hazırlama burada bulunur.', en: 'AI assistants: job and company research, automatic CV building, interview practice, and outreach drafting all live here.' },
  tour_back: { tr: 'Geri', en: 'Back' },
  tour_next: { tr: 'İleri', en: 'Next' },
  tour_continue: { tr: 'Devam Et', en: 'Continue' },

  // ── Profile Intake ──
  intake_title: { tr: 'Sizi Tanıyalım', en: "Let's Get to Know You" },
  intake_subtitle: { tr: 'Bu bilgiler ilan eşleştirme, ön yazı ve mülakat hazırlığında yapay zeka tarafından kullanılır. Yıldızlı alanlar zorunludur.', en: 'This information is used by AI for job matching, cover letters, and interview prep. Starred fields are required.' },
  intake_university: { tr: 'Üniversite', en: 'University' },
  intake_department: { tr: 'Bölüm', en: 'Department' },
  intake_graduation_year: { tr: 'Mezuniyet Yılı', en: 'Graduation Year' },
  intake_skills: { tr: 'Yetenekler', en: 'Skills' },
  intake_sectors: { tr: 'Hedef Sektörler', en: 'Target Sectors' },
  intake_languages: { tr: 'Diller', en: 'Languages' },
  intake_skill_placeholder: { tr: "Bir yetenek yazıp Enter'a basın...", en: 'Type a skill and press Enter...' },
  intake_sector_placeholder: { tr: "Bir sektör yazıp Enter'a basın...", en: 'Type a sector and press Enter...' },
  intake_language_placeholder: { tr: "Bir dil yazıp Enter'a basın...", en: 'Type a language and press Enter...' },
  intake_summary: { tr: 'Kısa Özet', en: 'Short Summary' },
  intake_continue: { tr: 'Devam Et', en: 'Continue' },
  intake_saving: { tr: 'Kaydediliyor...', en: 'Saving...' },
  intake_save_error: { tr: 'Kaydedilemedi. Lütfen tekrar deneyin.', en: 'Could not save. Please try again.' },
  intake_validation_hint: { tr: 'Devam etmek için üniversite, bölüm, en az bir yetenek ve en az bir hedef sektör girin.', en: 'To continue, enter your university, department, at least one skill, and at least one target sector.' },

  // ── Loading Screen ──
  loading_text: { tr: 'Yükleniyor...', en: 'Loading...' },
  loading_quote: { tr: '"İnsan için ancak çalıştığı kadarı vardır." (Necm Suresi, 53:39)', en: '"There is nothing for man except what he strives for." (Surah An-Najm, 53:39)' },

  // ── Error Boundary ──
  error_boundary_title: { tr: 'Bir Hata Oluştu', en: 'Something Went Wrong' },
  error_boundary_desc: { tr: 'Uygulama beklenmeyen bir hatayla karşılaştı. Lütfen sayfayı yenileyin ya da destek ile iletişime geçin.', en: 'The application encountered an unexpected error. Please refresh the page or contact support.' },
  error_boundary_details: { tr: 'Teknik Detaylar', en: 'Technical Details' },
  error_boundary_refresh: { tr: 'Yenile', en: 'Refresh' },
  error_boundary_home: { tr: 'Ana Sayfa', en: 'Home' },

  // ── App genel ──
  app_interview_simulator_label: { tr: 'MÜLAKAT SİMÜLATÖRÜ', en: 'INTERVIEW SIMULATOR' },
  app_footer_rights: { tr: 'Tüm Hakları Saklıdır.', en: 'All Rights Reserved.' },
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

function getInitialLanguage(): Language {
  const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return stored === 'en' || stored === 'tr' ? stored : 'tr';
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(getInitialLanguage);

  useEffect(() => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    // CSS text-transform:uppercase is locale-aware; without this, English text
    // stays uppercased under Turkish rules (e.g. "AUTOMATION" -> "AUTOMATİON").
    document.documentElement.lang = language;
  }, [language]);

  const setLanguage = (lang: Language) => setLanguageState(lang);

  const t = (key: string): string => {
    if (!translations[key]) {
      console.warn(`Translation key not found: ${key}`);
      return key;
    }
    return translations[key][language] || translations[key]['en'];
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
