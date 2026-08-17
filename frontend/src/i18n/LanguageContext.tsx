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
  app_title: { tr: 'Pusula', en: 'Pusula' },
  app_subtitle: { tr: 'Kariyer Yardımcısı', en: 'Career Copilot' },
  my_profile: { tr: 'Profilim', en: 'My Profile' },
  admin: { tr: 'Yönetici', en: 'Admin' },
  header_open_menu: { tr: 'Menüyü Aç', en: 'Open Menu' },
  header_close_menu: { tr: 'Menüyü Kapat', en: 'Close Menu' },
  header_light_theme: { tr: 'Açık temaya geç', en: 'Switch to light theme' },
  header_dark_theme: { tr: 'Koyu temaya geç', en: 'Switch to dark theme' },

  // ── Dashboard (Genel Bakış) ──
  dashboard_title: { tr: 'Genel Bakış', en: 'Overview' },
  dashboard_subtitle: { tr: 'Başvuru sürecinizin güncel özeti.', en: 'A current summary of your application process.' },
  dashboard_stat_total_jobs: { tr: 'Toplam İlan', en: 'Total jobs' },
  dashboard_stat_new_jobs: { tr: 'Yeni İlan', en: 'New jobs' },
  dashboard_stat_applications: { tr: 'Başvurular', en: 'Applications' },
  dashboard_stat_pending: { tr: 'Bekleyen Onay', en: 'Pending approval' },
  dashboard_scan_jobs: { tr: 'İlan Tara', en: 'Scan jobs' },
  dashboard_scanning: { tr: 'Taranıyor...', en: 'Scanning...' },
  dashboard_scan_inbox: { tr: 'Gelen Kutusunu Tara', en: 'Scan inbox' },
  dashboard_connect_gmail: { tr: 'Gmail Bağla', en: 'Connect Gmail' },
  dashboard_gmail_connected: { tr: 'Bağlı', en: 'Connected' },
  dashboard_cold_email: { tr: 'Soğuk E-posta', en: 'Cold email' },
  dashboard_top_matches: { tr: 'En İyi Eşleşme', en: 'Top match' },
  dashboard_see_all: { tr: 'Tümünü Gör', en: 'See All' },
  dashboard_prepare_application: { tr: 'Başvuru Hazırla', en: 'Prepare application' },
  dashboard_see_details: { tr: 'Detayları Gör', en: 'See details' },
  dashboard_no_matches_yet: { tr: 'Henüz bir eşleşme yok — ilan taramasını başlatın.', en: 'No matches yet — start a job scan.' },
  dashboard_other_matches: { tr: 'Diğer Eşleşmeler', en: 'Other Matches' },

  // ── Jobs (Fırsatlar) ──
  jobs_title: { tr: 'Fırsatlar', en: 'Opportunities' },
  jobs_active_suffix: { tr: 'Aktif İlan · Derin Tarama Hazır', en: 'Active Listings · Deep Scan Ready' },
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
  jobs_load_more: { tr: 'Daha Fazla Göster', en: 'Show More' },
  jobs_detail_title_fallback: { tr: 'İlan Detayı', en: 'Job details' },
  jobs_description: { tr: 'Açıklama', en: 'Description' },
  jobs_requirements: { tr: 'Gereksinimler', en: 'Requirements' },
  jobs_ai_evaluation: { tr: 'Yapay Zeka Değerlendirmesi', en: 'AI Evaluation' },
  jobs_prepare_application: { tr: 'Başvuru Hazırla', en: 'Prepare application' },
  jobs_preparing: { tr: 'Hazırlanıyor...', en: 'Preparing...' },
  jobs_prepare_error_fallback: { tr: 'Başvuru hazırlanamadı. Lütfen tekrar deneyin.', en: 'Could not prepare the application. Please try again.' },
  jobs_go_to_listing: { tr: 'İlana Git', en: 'View listing' },
  jobs_type_staj: { tr: 'Staj', en: 'Internship' },
  jobs_type_tam_zamanli: { tr: 'Tam Zamanlı', en: 'Full-time' },
  jobs_type_is: { tr: 'İş', en: 'Job' },
  jobs_status_new: { tr: 'Yeni', en: 'New' },
  jobs_status_reviewed: { tr: 'İncelendi', en: 'Reviewed' },
  jobs_status_applying: { tr: 'Başvuruluyor', en: 'Applying' },
  jobs_status_applied: { tr: 'Başvuruldu', en: 'Applied' },
  jobs_all_types: { tr: 'Tüm Türler', en: 'All Types' },
  jobs_all_cities: { tr: 'Tüm Şehirler', en: 'All Cities' },

  // ── Applications (Başvurular) ──
  applications_title: { tr: 'Başvuru Takip', en: 'Application Tracking' },
  applications_count_suffix: { tr: 'Başvuru · İş Akışı', en: 'Applications · Workflow' },
  applications_filter_all: { tr: 'Tümü', en: 'All' },
  applications_filter_label: { tr: 'Duruma göre filtrele', en: 'Filter by status' },
  applications_status_draft: { tr: 'Taslak', en: 'Draft' },
  applications_status_awaiting: { tr: 'Onay Bekliyor', en: 'Awaiting approval' },
  applications_status_approved: { tr: 'Onaylandı', en: 'Approved' },
  applications_status_submitted: { tr: 'Gönderildi', en: 'Submitted' },
  applications_empty_title: { tr: 'Henüz başvuru yok', en: 'No applications yet' },
  applications_empty_desc: { tr: 'İş ilanlarından başvuru hazırlayarak başlayın.', en: 'Get started by preparing an application from a job listing.' },
  applications_untitled_job: { tr: 'İsimsiz İlan', en: 'Untitled Listing' },
  applications_approve: { tr: 'Onayla', en: 'Approve' },
  applications_reject: { tr: 'Reddet', en: 'Reject' },
  applications_send: { tr: 'Gönder', en: 'Send' },
  applications_retry: { tr: 'Tekrar Dene', en: 'Retry' },
  applications_contact_email_label: { tr: 'Başvuru E-postası', en: 'Application Email' },
  applications_contact_email_placeholder: { tr: 'Bu ilan için e-posta bulunamadı — onaylarsan kopyala-yapıştır paketi hazırlanacak', en: 'No email found for this listing — approving will prepare a copy-paste package' },
  applications_source_job_posting: { tr: 'İlan içinden bulundu', en: 'Found in the job listing' },
  applications_source_web_search: { tr: "Web'de tahmin edildi — göndermeden önce kontrol edin", en: 'Guessed via web search — verify before sending' },
  applications_source_company_site: { tr: "Şirketin resmi sitesinde bulundu — göndermeden önce kontrol edin", en: "Found on the company's official site — verify before sending" },
  applications_source_manual: { tr: 'Elle girildi', en: 'Entered manually' },
  applications_copy: { tr: 'Kopyala', en: 'Copy' },
  applications_copied: { tr: 'Kopyalandı!', en: 'Copied!' },
  applications_qa_title: { tr: 'Kopyala-Yapıştıra Hazır Soru-Cevaplar', en: 'Copy-Paste-Ready Q&A' },
  applications_custom_qa_prompt: { tr: 'İlanın formunda başka sorular mı var? Cevaplayalım →', en: 'Does the listing form have other questions? Let us answer them →' },
  applications_custom_qa_hint: { tr: 'İlana gidip gördüğün gerçek soruları buraya, her satıra bir soru gelecek şekilde yapıştır.', en: 'Go to the listing and paste the real questions you see here, one per line.' },
  applications_custom_qa_placeholder: { tr: 'Örn: Bu pozisyon için neden özellikle bizi seçtiniz?', en: 'e.g. Why did you choose us specifically for this role?' },
  applications_custom_qa_cancel: { tr: 'Vazgeç', en: 'Cancel' },
  applications_custom_qa_submit: { tr: 'Cevapla', en: 'Answer' },
  applications_custom_qa_loading: { tr: 'Cevaplanıyor...', en: 'Answering...' },
  applications_custom_qa_error: { tr: 'Cevaplar üretilemedi, tekrar dene.', en: 'Could not generate answers, try again.' },
  applications_will_send_to: { tr: 'Gönderilecek adres:', en: 'Will send to:' },
  applications_send_failed_fallback: { tr: 'Gönderim başarısız oldu.', en: 'Sending failed.' },
  applications_manual_fallback_desc: { tr: 'Bu ilan için bir iletişim e-postası bulamadık — ilana giderek CV ve ön yazıyı kendin yapıştırman gerekiyor.', en: "We couldn't find a contact email for this listing — you'll need to go to the listing and paste in your CV and cover letter yourself." },
  applications_go_to_listing: { tr: 'İlana Git', en: 'View Listing' },
  applications_referral_prompt: { tr: 'Bu şirkette aynı üniversiteden biri var mı? Bulalım →', en: 'Anyone from your university at this company? Let’s find out →' },
  applications_referral_title: { tr: 'Mezun/Referans Bulucu', en: 'Alumni & Referral Finder' },
  applications_referral_refresh: { tr: 'Tekrar Ara', en: 'Search Again' },
  applications_referral_disclaimer: { tr: 'Bu sonuçlar yapay zeka tahmini olabilir — göndermeden önce LinkedIn\'de mutlaka doğrula.', en: 'These results may be AI guesses — always verify on LinkedIn before reaching out.' },
  applications_referral_empty: { tr: 'Bu şirkette aynı üniversiteden kimse bulunamadı.', en: 'No one from your university was found at this company.' },
  applications_referral_search_link: { tr: "LinkedIn'de Ara", en: 'Search on LinkedIn' },
  applications_referral_loading: { tr: 'Aranıyor...', en: 'Searching...' },
  applications_referral_error: { tr: 'Arama başarısız oldu, tekrar dene.', en: 'Search failed, try again.' },
  applications_followup_nudge: { tr: 'Bu başvuruya 10 gündür yanıt gelmedi.', en: "No response on this application in 10 days." },
  applications_followup_got_response: { tr: 'Yanıt Aldım', en: 'Got a Response' },
  applications_followup_draft_prompt: { tr: 'Takip e-postası hazırlayayım mı? →', en: 'Should I draft a follow-up email? →' },
  applications_followup_cancel: { tr: 'Vazgeç', en: 'Cancel' },
  applications_followup_send: { tr: 'Gönder', en: 'Send' },
  applications_followup_sending: { tr: 'Gönderiliyor...', en: 'Sending...' },
  applications_followup_loading: { tr: 'Hazırlanıyor...', en: 'Preparing...' },
  applications_followup_error: { tr: 'İşlem başarısız oldu, tekrar dene.', en: 'Something went wrong, try again.' },
  applications_followup_sent_confirm: { tr: 'Takip e-postası gönderildi. ✅', en: 'Follow-up email sent. ✅' },

  // ── Events (Etkinlikler) ──
  events_title: { tr: 'Etkinlikler', en: 'Events' },
  events_upcoming_suffix: { tr: 'Yaklaşan Etkinlik · Kariyer Takvimi', en: 'Upcoming Events · Career Calendar' },
  events_type_hackathon: { tr: 'Hackathon', en: 'Hackathon' },
  events_type_career_fair: { tr: 'Kariyer Fuarı', en: 'Career Fair' },
  events_type_seminar: { tr: 'Seminer', en: 'Seminar' },
  events_type_networking: { tr: 'Networking', en: 'Networking' },
  events_type_workshop: { tr: 'Atölye', en: 'Workshop' },
  events_empty_title: { tr: 'Henüz etkinlik bulunmuyor.', en: 'No events yet.' },
  events_empty_desc: { tr: 'Yaklaşan kariyer fuarları ve etkinlikler burada listelenecek.', en: 'Upcoming career fairs and events will be listed here.' },
  events_details_link: { tr: 'Etkinlik Detayları', en: 'Event Details' },

  // ── CV (Portföy) ──
  cv_title: { tr: 'Portföy', en: 'Portfolio' },
  cv_ats_active_suffix: { tr: 'CV · ATS Analizi Aktif', en: 'CVs · ATS Analysis Active' },
  cv_new_button: { tr: 'Yeni CV', en: 'New CV' },
  cv_empty_title: { tr: 'Henüz CV yüklenmemiş', en: 'No CV uploaded yet' },
  cv_empty_desc: { tr: 'Kariyer fırsatlarını değerlendirmek için bir CV yükleyin. Yapay zeka analizi anında başlayacaktır.', en: 'Upload a CV to start evaluating career opportunities. AI analysis will begin instantly.' },
  cv_default_badge: { tr: 'Varsayılan', en: 'Default' },
  cv_others_title: { tr: 'Diğer CV\'ler', en: 'Other CVs' },
  cv_performance_title: { tr: 'CV Türüne Göre Performans', en: 'Performance by CV Type' },
  cv_performance_applications: { tr: '{count} başvuru', en: '{count} applications' },
  cv_ai_generated_badge: { tr: 'Yapay Zeka ile Oluşturuldu', en: 'AI Generated' },
  cv_pdf: { tr: 'PDF', en: 'PDF' },
  cv_text: { tr: 'Metin', en: 'Text' },
  cv_detail_button: { tr: 'Detay', en: 'Details' },
  cv_detail_title_fallback: { tr: 'CV Detayı', en: 'CV details' },
  cv_ats_score: { tr: 'ATS Skoru', en: 'ATS Score' },
  cv_ats_pending: { tr: 'Analiz bekleniyor', en: 'Analysis pending' },
  cv_ai_feedback: { tr: 'Yapay Zeka Geri Bildirimi', en: 'AI Feedback' },
  cv_strengths: { tr: 'Güçlü Yönler', en: 'Strengths' },
  cv_weaknesses: { tr: 'İyileştirme Alanları', en: 'Areas for Improvement' },
  cv_content: { tr: 'CV İçeriği', en: 'CV Content' },
  cv_set_default: { tr: 'Varsayılan Yap', en: 'Set as default' },
  cv_delete: { tr: 'Sil', en: 'Delete' },
  cv_upload_title: { tr: 'Yeni CV Yükle', en: 'Upload new CV' },
  cv_upload_desc: { tr: 'PDF formatındaki özgeçmişinizi sisteme entegre edin. Yapay zeka otomatik analiz yapacak.', en: 'Integrate your PDF resume into the system. AI will analyze it automatically.' },
  cv_variant_general: { tr: 'Genel Özgeçmiş', en: 'General Resume' },
  cv_variant_ai: { tr: 'Yapay Zeka Odaklı', en: 'AI-Focused' },
  cv_variant_cyber: { tr: 'Siber Güvenlik Odaklı', en: 'Cybersecurity-Focused' },
  cv_variant_it: { tr: 'IT & Sistem Yönetimi', en: 'IT & Systems Administration' },
  cv_analyzing: { tr: 'Analiz Yapılıyor...', en: 'Analyzing...' },
  cv_upload_and_analyze: { tr: 'Yükle ve Analiz Et', en: 'Upload and analyze' },
  cv_upload_file_label: { tr: 'PDF dosyası seç', en: 'Choose PDF file' },
  cv_variant_select_label: { tr: 'CV türü', en: 'CV type' },

  // ── Inbox (Gelen Kutusu) ──
  inbox_title: { tr: 'Gelen Kutusu', en: 'Inbox' },
  inbox_opportunities_suffix: { tr: 'Kariyer Fırsatı · Yapay Zeka Taraması', en: 'Career Opportunities · AI Scanning' },
  inbox_syncing: { tr: 'Senkronize Ediliyor...', en: 'Syncing...' },
  inbox_sync: { tr: 'Senkronize Et', en: 'Sync' },
  inbox_empty_title: { tr: 'Henüz kariyer fırsatı bulunamadı.', en: 'No career opportunities found yet.' },
  inbox_empty_desc: { tr: 'Gmail hesabınızı bağlayarak e-postalarınızı tarayın.', en: 'Connect your Gmail account to scan your emails.' },
  inbox_type_job: { tr: 'İş İlanı', en: 'Job listing' },
  inbox_type_event: { tr: 'Etkinlik', en: 'Event' },
  inbox_type_hackathon: { tr: 'Hackathon', en: 'Hackathon' },
  inbox_type_career_fair: { tr: 'Kariyer Fuarı', en: 'Career fair' },
  inbox_type_course: { tr: 'Eğitim', en: 'Course' },
  inbox_type_update: { tr: 'Güncelleme', en: 'Update' },

  // ── AI Asistanları (Otomasyon) ──
  agents_title: { tr: 'Yapay Zeka Asistanları', en: 'AI Assistants' },
  agents_subtitle: { tr: 'Kariyer yolculuğunuzu hızlandırmak için geliştirilmiş yapay zeka araçları.', en: 'AI-powered tools built to accelerate your career journey.' },
  agents_start_button: { tr: 'Başlat', en: 'Start' },
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
  interview_technical_badge: { tr: 'Teknik', en: 'Technical' },
  interview_cultural_badge: { tr: 'Kültürel', en: 'Cultural' },
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
  profile_restart_tour: { tr: 'Turu Tekrar Başlat', en: 'Restart Tour' },
  profile_identity_title: { tr: 'Kimlik ve Akademik Bilgiler', en: 'Identity and Academic Information' },
  profile_identity_desc: { tr: 'Bu bilgiler ön yazı ve mülakat hazırlığında yapay zeka tarafından kullanılır.', en: 'This information is used by AI when preparing cover letters and interviews.' },
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
  profile_integrations_title: { tr: 'Entegrasyonlar', en: 'Integrations' },
  profile_integrations_desc: { tr: 'Otomasyon süreçleri için gerekli yapay zeka bağlantıları.', en: 'AI connections required for automation workflows.' },
  profile_gemini_key_title: { tr: 'Gemini API Anahtarı', en: 'Gemini API Key' },
  profile_gemini_key_desc: { tr: 'Kendi anahtarını girersen yapay zeka özellikleri (CV analizi, eşleştirme, mektup, mülakat vb.) paylaşılan kota yerine senin kendi kotanı kullanır.', en: 'If you enter your own key, AI features (CV analysis, matching, cover letters, interviews, etc.) use your own quota instead of the shared one.' },
  profile_gemini_key_badge_active: { tr: 'Aktif', en: 'Active' },
  profile_gemini_key_active: { tr: 'Bir anahtar kayıtlı ve kullanılıyor', en: 'A key is saved and in use' },
  profile_gemini_key_placeholder_set: { tr: 'Değiştirmek için yeni anahtar gir...', en: 'Enter a new key to change it...' },
  profile_gemini_key_placeholder_empty: { tr: 'AIzaSy... veya AQ....', en: 'AIzaSy... or AQ....' },
  profile_gemini_key_remove: { tr: 'Kaldır', en: 'Remove' },
  profile_gemini_key_renew: { tr: 'Yenile', en: 'Renew' },
  profile_gemini_key_get_one: { tr: 'Ücretsiz anahtar almak için Google AI Studio\'ya git', en: 'Get a free key from Google AI Studio' },
  profile_edit: { tr: 'Düzenle', en: 'Edit' },
  profile_gemini_key_show: { tr: 'Anahtarı göster', en: 'Show key' },
  profile_gemini_key_hide: { tr: 'Anahtarı gizle', en: 'Hide key' },
  profile_cancel: { tr: 'İptal', en: 'Cancel' },
  profile_completeness: { tr: 'Profil Doluluğu', en: 'Profile Completeness' },
  profile_additional_title: { tr: 'Beceriler & Tercihler', en: 'Skills & Preferences' },
  profile_additional_desc: { tr: 'Eşleştirme ve içerik üretimi bu bilgilere göre kişiselleştirilir.', en: 'Matching and content generation are personalized using this information.' },
  profile_discard: { tr: 'Değişiklikleri Geri Al', en: 'Discard Changes' },
  profile_save: { tr: 'Profili Kaydet', en: 'Save Profile' },
  profile_saving: { tr: 'Kaydediliyor...', en: 'Saving...' },
  profile_saved: { tr: 'Kaydedildi!', en: 'Saved!' },
  profile_save_error: { tr: 'Profil kaydedilemedi.', en: 'Profile could not be saved.' },

  // ── Gmail Modal ──
  gmail_modal_title: { tr: 'Gmail Bağlantısı', en: 'Connect Gmail' },
  gmail_modal_info: { tr: 'Gmail hesabınızı bağlamak için "Uygulama Şifresi" kullanmalısınız.', en: 'You must use an "App Password" to connect your Gmail account.' },
  gmail_modal_info_path: { tr: 'Google Hesabı > Güvenlik > 2 Adımlı Doğrulama > Uygulama Şifreleri', en: 'Google Account > Security > 2-Step Verification > App Passwords' },
  gmail_modal_email_placeholder: { tr: 'Gmail Adresiniz', en: 'Your Gmail Address' },
  gmail_modal_password_placeholder: { tr: 'Uygulama Şifresi (16 Haneli)', en: 'App Password (16 characters)' },
  gmail_modal_connecting: { tr: 'Bağlanıyor...', en: 'Connecting...' },
  gmail_modal_connect: { tr: 'Hesabı Bağla', en: 'Connect account' },

  // ── Outreach Modal ──
  outreach_modal_title: { tr: 'Soğuk Başvuru', en: 'Cold Application' },
  outreach_modal_info: { tr: 'Hedef şirketin İK e-posta adresini otomatik bulur ve yapay zeka ile özel bir önyazı hazırlar — göndermeden önce inceleyip onaylarsınız.', en: "Automatically finds the target company's HR email and prepares a tailored cover letter with AI — you review and approve it before anything is sent." },
  outreach_modal_company_label: { tr: 'Şirket Adı', en: 'Company Name' },
  outreach_modal_company_placeholder: { tr: 'Örn: Baykar, Turkcell, Garanti BBVA...', en: 'e.g. Google, Amazon, Microsoft...' },
  outreach_modal_sending: { tr: 'Gönderiliyor...', en: 'Sending...' },
  outreach_modal_send: { tr: 'Soğuk E-posta Gönder', en: 'Send cold email' },
  outreach_modal_preparing: { tr: 'Hazırlanıyor...', en: 'Preparing...' },
  outreach_modal_prepare_button: { tr: 'Taslak Hazırla', en: 'Prepare draft' },
  outreach_modal_review_hint: { tr: 'Göndermeden önce gözden geçirin — alıcı e-postasını gerekirse düzeltebilirsiniz.', en: 'Review before sending — you can correct the recipient email if needed.' },
  outreach_modal_target_email_label: { tr: 'Alıcı E-posta', en: 'Recipient Email' },
  outreach_modal_subject_label: { tr: 'Konu', en: 'Subject' },
  outreach_modal_body_label: { tr: 'Mesaj Önizlemesi', en: 'Message Preview' },
  outreach_modal_approve_send: { tr: 'Onayla ve Gönder', en: 'Approve & send' },
  outreach_modal_back: { tr: 'Geri', en: 'Back' },
  outreach_modal_success: { tr: 'E-posta gönderildi.', en: 'Email sent.' },
  outreach_modal_close: { tr: 'Kapat', en: 'Close' },

  // ── Auth ──
  auth_subtitle: { tr: 'Kurumsal Hesap Girişi', en: 'Enterprise Account Login' },
  auth_login_tab: { tr: 'Giriş Yap', en: 'Log In' },
  auth_register_tab: { tr: 'Üye Ol', en: 'Sign Up' },
  auth_full_name: { tr: 'Ad Soyad', en: 'Full Name' },
  auth_full_name_placeholder: { tr: 'Adınız Soyadınız', en: 'Your Full Name' },
  auth_email: { tr: 'E-Posta', en: 'Email' },
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
  onboarding_intro: { tr: 'Pusula; veri odaklı analizler, başvuru hazırlığı ve mülakat provalarıyla profesyonel gelişiminizi tek platformdan yönetmenizi sağlar.', en: 'Pusula lets you manage your professional growth from a single platform — with data-driven analysis, application preparation, and interview rehearsal.' },
  onboarding_feature_cv_title: { tr: "ATS Uyumlu CV'ler", en: 'ATS-Compliant CVs' },
  onboarding_feature_cv_desc: { tr: 'Kurumsal başvuru takip sistemlerinden geçebilen, algoritma dostu özgeçmişler oluşturur.', en: 'Generates algorithm-friendly resumes that pass enterprise applicant tracking systems.' },
  onboarding_feature_radar_title: { tr: 'Otomatik İlan Takibi', en: 'Automatic Job Tracking' },
  onboarding_feature_radar_desc: { tr: 'Yerel ve küresel iş piyasasını sürekli tarayarak yetkinliklerinize uygun ilanları bulur.', en: 'Continuously scans local and global job markets to find listings matching your skills.' },
  onboarding_feature_inbox_title: { tr: 'Akıllı Gelen Kutusu', en: 'Smart Inbox' },
  onboarding_feature_inbox_desc: { tr: 'Gelen iş teklifi ve mülakat davetlerini yapay zeka ile otomatik sınıflandırır.', en: 'Automatically classifies incoming job offers and interview invitations with AI.' },
  onboarding_start_button: { tr: 'Başlayalım', en: "Let's Start" },

  tour_back: { tr: 'Geri', en: 'Back' },
  tour_next: { tr: 'İleri', en: 'Next' },

  // ── Maskotlu Rehber Tur (v2) ──
  tour_v2_step_label: { tr: 'Adım', en: 'Step' },
  tour_v2_skip: { tr: 'Turu Geç', en: 'Skip Tour' },
  tour_v2_finish: { tr: 'Tamamla', en: 'Finish' },
  tour_v2_welcome_title: { tr: 'Merhaba, ben Pusula!', en: "Hi, I'm Pusula!" },
  tour_v2_welcome_desc: { tr: 'Sana burada nasıl yardımcı olacağımı hızlıca göstereyim mi? Sadece birkaç adım sürer.', en: 'Want me to quickly show you around? It only takes a few steps.' },
  tour_v2_dashboard_title: { tr: 'Yönetim Paneli', en: 'Dashboard' },
  tour_v2_dashboard_desc: { tr: 'Sana özel en iyi eşleşmeyi ve genel durumunu burada tek bakışta gösteririm.', en: 'I show your best match and overall status here at a glance.' },
  tour_v2_jobs_title: { tr: 'Fırsatlar', en: 'Opportunities' },
  tour_v2_jobs_desc: { tr: 'Bulduğum yeni ilanlar burada — her birini senin CV\'ne göre puanlarım.', en: 'New listings I find live here — I score each one against your CV.' },
  tour_v2_applications_title: { tr: 'Başvurular', en: 'Applications' },
  tour_v2_applications_desc: { tr: 'Hazırladığım her başvuruyu göndermeden önce mutlaka senin onayına sunarım.', en: 'I always ask for your approval before sending any application I prepare.' },
  tour_v2_events_title: { tr: 'Etkinlikler', en: 'Events' },
  tour_v2_events_desc: { tr: 'Kariyer fuarlarını ve etkinlikleri kaçırmaman için takvimini burada tutarım.', en: 'I keep your calendar here so you never miss a career fair or event.' },
  tour_v2_cv_title: { tr: 'Portföy', en: 'Portfolio' },
  tour_v2_cv_desc: { tr: 'CV\'lerini burada saklarım, her biri için ATS uyum puanı çıkarırım.', en: 'I keep your CVs here and score each one for ATS compatibility.' },
  tour_v2_inbox_title: { tr: 'Gelen Kutusu', en: 'Inbox' },
  tour_v2_inbox_desc: { tr: 'Gmail\'ini bağlarsan, iş fırsatlarını e-postalarından da yakalarım.', en: "If you link Gmail, I'll catch job opportunities from your emails too." },
  tour_v2_agents_title: { tr: 'Otomasyon', en: 'Automation' },
  tour_v2_agents_desc: { tr: 'Araştırma, mülakat provası, e-posta taslağı... asistanlarım burada seni bekliyor.', en: 'Research, interview practice, outreach drafts... my assistants are here for you.' },
  tour_v2_done_title: { tr: 'Hazırsın!', en: "You're all set!" },
  tour_v2_done_desc: { tr: 'Artık her şeyi biliyorsun. İstediğin zaman profilinden turu tekrar başlatabilirsin.', en: "You know your way around now. You can restart this tour anytime from your profile." },

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
  app_interview_simulator_label: { tr: 'Mülakat Simülatörü', en: 'Interview Simulator' },
  app_footer_rights: { tr: 'Tüm Hakları Saklıdır.', en: 'All Rights Reserved.' },
  app_gmail_link_error: { tr: 'Gmail hesabı bağlanamadı.', en: 'Could not connect the Gmail account.' },

  // ── Ortak hata/bağlantı mesajları (hook'lar) ──
  common_request_failed: { tr: 'İstek başarısız oldu', en: 'Request failed' },
  common_sse_disconnected: { tr: 'Sunucu bağlantısı kesildi.', en: 'Server connection was lost.' },
  ws_connected: { tr: 'Ajan sistemi bağlantısı kuruldu.', en: 'Agent system connected.' },
  ws_reconnecting: { tr: 'Bağlantı kesildi. Yeniden bağlanılıyor...', en: 'Connection lost. Reconnecting...' },
  ws_error: { tr: 'WebSocket bağlantı hatası.', en: 'WebSocket connection error.' },
  modal_close: { tr: 'Modalı Kapat', en: 'Close Modal' },
  outreach_fallback_company: { tr: 'Hedef Şirket', en: 'Target Company' },
  outreach_fallback_position: { tr: 'Pozisyon', en: 'Position' },
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

// React dışı yerlerde (modül seviyesi fetch yardımcıları, hook'lar) dil
// tercihine erişmek için: useLanguage() bir bileşen içinde çağrılmalı, ama
// örn. apiPost gibi düz fonksiyonlar bileşen değil — bunlar için localStorage'ı
// doğrudan okuyan bu statik yardımcıyı kullanıyoruz.
export function translateStatic(key: string): string {
  const entry = translations[key];
  if (!entry) return key;
  return entry[getInitialLanguage()] || entry['en'];
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
