import json
import logging
import asyncio
from typing import List, Optional

import google.generativeai as genai
from pydantic import BaseModel, ValidationError

from backend.config import settings
from backend.exceptions import AIServiceError, TimeoutError as KariyerTimeoutError, ValidationError as KariyerValidationError

# Loglama yapılandırması (Print yerine standart logging kullanımı)
logger = logging.getLogger("KariyerAjani.AI")

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


# Pydantic V2 Modelleri
class CVAnalysisResult(BaseModel):
    score: float
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    keywords: List[str]
    improvement_tips: List[str]


class JobMatchResult(BaseModel):
    score: float
    explanation: str
    matching_skills: List[str]
    missing_skills: List[str]
    recommendation: str


def _get_model(require_json: bool = False):
    """
    Gemini model instance'ı oluşturur. 
    Eğer require_json True ise API'nin kesinlikle JSON dönmesini sağlayan konfigürasyonu ekler.
    """
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json" if require_json else "text/plain"
    )
    return genai.GenerativeModel(
        settings.GEMINI_MODEL,
        generation_config=generation_config
    )


def _sanitize_prompt_text(text: Optional[str]) -> str:
    """Prompt limitlerini aşmamak için metni güvenli hale getirir."""
    if not text:
        return ""
    cleaned = text.strip()
    return cleaned[:20000] if len(cleaned) > 20000 else cleaned


async def _call_model_async_json(prompt: str, timeout_seconds: int = 30) -> dict:
    """Asenkron olarak modeli çağırır ve her zaman dict (JSON) döner."""
    try:
        model = _get_model(require_json=True)
        # Timeout ile async çağrı
        response = await asyncio.wait_for(
            model.generate_content_async(prompt),
            timeout=timeout_seconds
        )
        
        if not response or not getattr(response, "text", None):
            raise AIServiceError("Gemini modelinden boş yanıt döndü.")
            
        return json.loads(response.text)
    
    except asyncio.TimeoutError:
        logger.error(f"Gemini API timeout (>{timeout_seconds}s)")
        raise KariyerTimeoutError(f"AI service timeout after {timeout_seconds} seconds")
    
    except json.JSONDecodeError as e:
        logger.error(f"Gemini çıktısı JSON formatında değildi: {e}")
        raise KariyerValidationError(f"Invalid JSON response from AI: {e}")
    
    except (ValueError, TypeError) as e:
        logger.error(f"Gemini API validation error: {e}")
        raise KariyerValidationError(f"AI service validation error: {e}")
    
    except Exception as e:
        logger.error(f"Gemini API çağrısında hata: {type(e).__name__} - {e}")
        raise AIServiceError(f"AI service error: {str(e)}")


async def analyze_cv_ats(cv_text: str) -> dict:
    """
    ATS skorlama: CV metnini analiz et, skor ve geri bildirim ver.
    Returns: {score, feedback, strengths, weaknesses, keywords}
    """
    safe_cv = _sanitize_prompt_text(cv_text)
    
    prompt = f"""Sen bir ATS (Applicant Tracking System) uzmanısın.
Aşağıdaki CV'yi analiz et.

ATS kriterleri:
- Anahtar kelime yoğunluğu
- Format ve yapı (bölümler açık mı?)
- Ölçülebilir başarılar
- Beceri eşleştirme potansiyeli
- Gramer ve profesyonellik

CV Metni:
{safe_cv}
"""

    try:
        result_dict = await _call_model_async_json(prompt)
        # Pydantic V2 kullanımı: model_validate
        validated = CVAnalysisResult.model_validate(result_dict)
        return validated.model_dump()
        
    except (KariyerValidationError, AIServiceError, KariyerTimeoutError) as e:
        logger.warning(f"AI Analizi başarısız oldu, basit algoritmaya dönülüyor. Hata: {e}")

        # Fallback Algoritması
        text_lower = (cv_text or "").lower()
        base_score = 40
        keywords = {
            "python": 5, "sql": 5, "react": 5, "javascript": 4, "java": 4,
            "staj": 10, "proje": 8, "deneyim": 5, "eğitim": 5, "analiz": 5,
            "yönetim": 4, "bilişim": 4, "sistem": 4, "makine öğrenmesi": 6,
            "siber": 6, "güvenlik": 6, "linux": 4, "docker": 5, "git": 4,
        }
        
        found_keywords = [k for k in keywords if k in text_lower]
        keyword_bonus = sum(keywords[k] for k in found_keywords)
        length_score = min(15, len(text_lower) // 300)
        final_score = min(92, base_score + keyword_bonus + length_score)

        return {
            "score": float(final_score),
            "feedback": "AI analizi şu an yapılamıyor. Anahtar kelime tabanlı algoritmik değerlendirme kullanıldı.",
            "strengths": ["Belge metni başarıyla okundu", f"{len(found_keywords)} kritik anahtar kelime tespit edildi"],
            "weaknesses": ["Derin AI analizi gerçekleştirilemedi."],
            "keywords": found_keywords,
            "improvement_tips": ["API bağlantınızı kontrol edin."],
        }


async def match_job_to_cv(job_description: str, cv_text: str, user_skills: List[str]) -> dict:
    """
    İlan-CV eşleştirme: uyum skoru ve en iyi eşleşmeyi hesapla.
    """
    safe_job = _sanitize_prompt_text(job_description)
    safe_cv = _sanitize_prompt_text(cv_text)
    safe_skills = [skill.strip() for skill in (user_skills or []) if skill.strip()]

    prompt = f"""Sen bir kariyer danışmanısın. Aşağıdaki iş ilanı ile adayın CV'sini karşılaştır ve adayın becerilerini değerlendir.
Adayın Becerileri: {', '.join(safe_skills)}

İş İlanı:
{safe_job}

CV:
{safe_cv}
"""

    try:
        result_dict = await _call_model_async_json(prompt)
        validated = JobMatchResult.model_validate(result_dict)
        return validated.model_dump()
        
    except (KariyerValidationError, AIServiceError, KariyerTimeoutError) as e:
        logger.warning(f"İş Eşleştirme başarısız oldu, basit algoritmaya dönülüyor. Hata: {e}")

        job_lower = safe_job.lower()
        cv_lower = safe_cv.lower()
        matching = [s for s in safe_skills if s.lower() in job_lower and s.lower() in cv_lower]

        base_match = 35 if safe_job else 0
        final_score = min(88, base_match + (len(matching) * 8))

        return {
            "score": float(final_score),
            "explanation": "AI eşleştirmesi yapılamadı. Temel metin örtüşme algoritması kullanıldı.",
            "matching_skills": matching,
            "missing_skills": ["Sistem ulaşılamaz durumda"],
            "recommendation": "Becerileriniz ilanla temel düzeyde örtüşüyor." if final_score > 50 else "İlanı manuel inceleyin."
        }


async def generate_cover_letter(
    job_title: str,
    company_name: str,
    job_description: str,
    cv_text: str,
    user_name: str,
    university: str,
    department: str,
) -> str:
    """Şirkete özel motivasyon mektubu üret."""
    prompt = f"""Sen profesyonel bir kariyer danışmanısın. Aşağıdaki bilgilere göre Türkçe bir motivasyon mektubu yaz.
- 250-350 kelime.
- Şirketin özelliklerine referans ver.
- 'Sayın İnsan Kaynakları Yetkilisi,' ile başla.
- Ek açıklama ekleme, sadece mektup metnini yaz.

Aday: {user_name}
Eğitim: {university} - {department}
Şirket: {company_name}
Pozisyon: {job_title}

İlan Detayı: {job_description}
Adayın CV'si: {cv_text}
"""

    try:
        model = _get_model(require_json=False)
        response = await asyncio.wait_for(
            model.generate_content_async(prompt),
            timeout=30
        )
        return response.text.strip()
    
    except asyncio.TimeoutError:
        logger.error("Cover letter generation timeout")
        raise KariyerTimeoutError("Cover letter generation timed out")
    
    except Exception as e:
        logger.error(f"Motivasyon mektubu üretilemedi: {type(e).__name__} - {e}")
        return f"""Sayın İnsan Kaynakları Yetkilisi,

{company_name} bünyesinde ilan edilen {job_title} pozisyonu ile yakından ilgileniyorum. {university} {department} öğrencisi olarak edindiğim yetkinlikleri şirketinizin hedefleriyle birleştirmek istiyorum.

İlgili gereksinimlerin kariyer profilimle örtüştüğüne inanıyorum. Değerli vaktinizi ayırdığınız için teşekkür eder, olumlu dönüşlerinizi beklerim.

Saygılarımla,
{user_name}"""


async def generate_cold_email(
    company_name: str,
    cv_text: str,
    user_name: str,
    university: str,
    department: str,
) -> str:
    """Şirkete özel soğuk başvuru e-postası üret."""
    prompt = f"""Sen proaktif bir kariyer uzmanısın. Açık ilanı olmayan bir şirkete staj/proje başvurusu yapmak için etkileyici bir "Soğuk İletişim E-postası" oluştur.
- Maksimum 250 kelime.
- HTML veya Markdown kullanma.
- 'Sayın İlgili,' ile başla.

Aday: {user_name}
Eğitim: {university}, {department}
Hedef Şirket: {company_name}

Adayın CV'si:
{cv_text}
"""

    try:
        model = _get_model(require_json=False)
        response = await asyncio.wait_for(
            model.generate_content_async(prompt),
            timeout=30
        )
        return response.text.strip()
    
    except asyncio.TimeoutError:
        logger.error("Cold email generation timeout")
        raise KariyerTimeoutError("Cold email generation timed out")
    
    except Exception as e:
        logger.error(f"Soğuk e-posta oluşturulamadı: {type(e).__name__} - {e}")
        return "[Hata] E-posta üretim servisine şu an ulaşılamıyor. Lütfen daha sonra tekrar deneyin."


async def generate_cv_content(
    user_name: str,
    email: str,
    phone: str,
    university: str,
    department: str,
    skills: List[str],
    variant_type: str,
    experience: str = "",
    projects: str = "",
) -> str:
    """AI ile CV içeriği oluştur — belirli varyant tipine göre."""
    
    variant_descriptions = {
        "ai": "Yapay Zeka ve Veri Bilimi odaklı (Python, ML, veri analizi)",
        "cyber": "Siber Güvenlik odaklı (ağ güvenliği, penetrasyon testi)",
        "it": "IT ve Sistem Yönetimi odaklı (altyapı, bulut, DevOps)",
        "general": "Genel YBS/Proje Mühendisliği odaklı (iş analizi, proje yönetimi, süreç iyileştirme)",
    }

    focus = variant_descriptions.get(variant_type, variant_descriptions["general"])

    prompt = f"""Sen profesyonel bir CV yazarısın. Aşağıdaki bilgilere göre {focus} bir CV oluştur.
- Markdown formatında düzenli bölümler kullan (Kişisel Bilgiler, Eğitim, Deneyim, Projeler, Teknik Beceriler).
- ATS uyumlu anahtar kelimelere yer ver.

Ad Soyad: {user_name}
İletişim: {email} | {phone}
Eğitim: {university} - {department}
Beceriler: {', '.join(skills)}
Deneyim: {experience or 'Belirtilmedi'}
Projeler: {projects or 'Belirtilmedi'}
"""

    try:
        model = _get_model(require_json=False)
        response = await asyncio.wait_for(
            model.generate_content_async(prompt),
            timeout=30
        )
        return response.text.strip()
    
    except asyncio.TimeoutError:
        logger.error("CV content generation timeout")
        raise KariyerTimeoutError("CV generation timed out")
    
    except Exception as e:
        logger.error(f"CV içeriği üretilemedi: {type(e).__name__} - {e}")
        return "[Hata] Özgeçmiş üretilirken API limitlerine takıldık veya sunucu yanıt vermedi."