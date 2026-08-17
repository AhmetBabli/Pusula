import json
import logging
import asyncio
from typing import List, Optional

from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from pydantic import BaseModel, ValidationError

from backend.config import settings
from backend.exceptions import AIServiceError, TimeoutError as KariyerTimeoutError, ValidationError as KariyerValidationError

# Loglama yapılandırması (Print yerine standart logging kullanımı)
logger = logging.getLogger("KariyerAjani.AI")


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


def _get_client(api_key: Optional[str] = None) -> genai.Client:
    """Kullanıcının kendi Gemini key'i ile (varsa) bir client döner — yoksa
    backend'in paylaşılan .env key'ine düşer. Eski `google.generativeai`
    kütüphanesinin aksine burada global bir `configure()` yok; her istek
    kendi client'ını kuruyor, bu yüzden farklı kullanıcıların key'leri eş
    zamanlı isteklerde birbirine karışmıyor (thread/request-safe)."""
    return genai.Client(api_key=api_key or settings.GEMINI_API_KEY)


def _sanitize_prompt_text(text: Optional[str]) -> str:
    """Prompt limitlerini aşmamak için metni güvenli hale getirir."""
    if not text:
        return ""
    cleaned = text.strip()
    return cleaned[:20000] if len(cleaned) > 20000 else cleaned


async def _call_model_async_json(prompt: str, timeout_seconds: int = 30, api_key: Optional[str] = None) -> dict:
    """Asenkron olarak modeli çağırır ve her zaman dict (JSON) döner.
    Gemini'nin geçici "high demand" (503) yanıtları için kısa aralıklarla
    en fazla 2 kez daha dener — Google'ın kendi hata mesajı bu hatanın
    genelde birkaç saniye içinde geçtiğini söylüyor."""
    client = _get_client(api_key)
    for attempt in range(3):
        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                ),
                timeout=timeout_seconds,
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

        except genai_errors.ServerError as e:
            if attempt < 2:
                logger.warning(f"Gemini geçici olarak meşgul (deneme {attempt + 1}/3), tekrar deneniyor: {e}")
                await asyncio.sleep(2 * (attempt + 1))
                continue
            logger.error(f"Gemini API sürekli meşgul, vazgeçildi: {e}")
            raise AIServiceError(f"AI service temporarily unavailable: {e}")

        except Exception as e:
            logger.error(f"Gemini API çağrısında hata: {type(e).__name__} - {e}")
            raise AIServiceError(f"AI service error: {str(e)}")


async def analyze_cv_ats(cv_text: str, api_key: Optional[str] = None) -> dict:
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

Yanıtını KESİNLİKLE aşağıdaki JSON şemasıyla ver. Anahtar adlarını AYNEN
kullan (İngilizce), değiştirme veya çevirme — sadece değerler Türkçe olsun:
{{
  "score": <0-100 arası sayı>,
  "feedback": "<genel değerlendirme, 2-3 cümle>",
  "strengths": ["<güçlü yön>", ...],
  "weaknesses": ["<zayıf yön>", ...],
  "keywords": ["<tespit edilen anahtar kelime>", ...],
  "improvement_tips": ["<somut öneri>", ...]
}}
"""

    try:
        result_dict = await _call_model_async_json(prompt, api_key=api_key)
        # Pydantic V2 kullanımı: model_validate
        validated = CVAnalysisResult.model_validate(result_dict)
        return {**validated.model_dump(), "ai_powered": True}

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
            "ai_powered": False,
        }


async def match_job_to_cv(job_description: str, cv_text: str, user_skills: List[str], api_key: Optional[str] = None) -> dict:
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

Yanıtını KESİNLİKLE aşağıdaki JSON şemasıyla ver. Anahtar adlarını AYNEN
kullan (İngilizce), değiştirme veya çevirme — sadece değerler Türkçe olsun:
{{
  "score": <0-100 arası sayı>,
  "explanation": "<eşleşme değerlendirmesi, 2-3 cümle>",
  "matching_skills": ["<örtüşen beceri>", ...],
  "missing_skills": ["<eksik beceri>", ...],
  "recommendation": "<kısa tavsiye>"
}}
"""

    try:
        result_dict = await _call_model_async_json(prompt, api_key=api_key)
        validated = JobMatchResult.model_validate(result_dict)
        return {**validated.model_dump(), "ai_powered": True}

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
            "recommendation": "Becerileriniz ilanla temel düzeyde örtüşüyor." if final_score > 50 else "İlanı manuel inceleyin.",
            "ai_powered": False,
        }


async def match_jobs_batch(jobs: List[dict], cv_text: str, user_skills: List[str], api_key: Optional[str] = None) -> dict:
    """
    Birden fazla ilanı TEK Gemini isteğinde CV ile eşleştirir (kota tasarrufu için —
    her ilanı ayrı ayrı sormak yerine bir grubu tek istekte işler).

    jobs: [{"id": <çağıranın kendi anahtarı, örn. Job.id>, "description": <ilan metni>}, ...]
    Döner: {job_id: {"score":..., "explanation":..., "matching_skills":..., "missing_skills":...,
                      "recommendation":..., "ai_powered": True}}
    Modelin atladığı/parse edilemeyen ilanlar sözlükte yer almaz — çağıran taraf bunun
    için kendi (AI'sız) yedek mantığına düşebilir.
    """
    if not jobs:
        return {}

    safe_cv = _sanitize_prompt_text(cv_text)
    safe_skills = [skill.strip() for skill in (user_skills or []) if skill.strip()]

    jobs_block = "\n\n".join(
        f"### İLAN #{j['id']}\n{_sanitize_prompt_text(j['description'])[:3000]}"
        for j in jobs
    )

    prompt = f"""Sen bir kariyer danışmanısın. Aşağıda bir adayın becerileri, CV'si ve
BİRDEN FAZLA iş ilanı var. Adayın CV'sini HER ilanla AYRI AYRI karşılaştır.

Adayın Becerileri: {', '.join(safe_skills)}

Adayın CV'si:
{safe_cv}

{jobs_block}

Yanıtını KESİNLİKLE şu JSON formatında ver — "results" dizisinde yukarıda gördüğün
HER ilan için bir kayıt olsun, "job_id" alanı o ilanın "İLAN #N" numarasıyla
BİREBİR aynı olsun, hiçbirini atlama:
{{"results": [
  {{"job_id": <N>, "score": <0-100 arası sayı>, "explanation": "<2-3 cümle>",
    "matching_skills": ["..."], "missing_skills": ["..."], "recommendation": "<kısa tavsiye>"}}
]}}"""

    results: dict = {}
    try:
        data = await _call_model_async_json(prompt, timeout_seconds=45, api_key=api_key)
        for item in data.get("results", []):
            try:
                job_id = int(item.get("job_id"))
                validated = JobMatchResult.model_validate(item)
                results[job_id] = {**validated.model_dump(), "ai_powered": True}
            except (ValueError, TypeError, ValidationError):
                continue
    except Exception as e:
        logger.warning(f"Toplu iş eşleştirme başarısız oldu: {type(e).__name__} - {e}")

    return results


async def generate_cover_letter(
    job_title: str,
    company_name: str,
    job_description: str,
    cv_text: str,
    user_name: str,
    university: str,
    department: str,
    api_key: Optional[str] = None,
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
        client = _get_client(api_key)
        response = await asyncio.wait_for(
            client.aio.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt),
            timeout=30,
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


async def generate_application_qa(
    job_title: str,
    company_name: str,
    job_description: str,
    cv_text: str,
    user_name: str,
    university: str,
    department: str,
    api_key: Optional[str] = None,
    custom_questions: Optional[List[str]] = None,
) -> list:
    """Başvuru formlarında sıkça sorulan sorulara, adayın CV'sine ve ilana özel
    kopyala-yapıştıra hazır Türkçe cevaplar üretir. `custom_questions` verilirse
    (kullanıcı ilanın kendi formundaki gerçek soruları yapıştırdıysa) sabit 5
    genel soru yerine SADECE o sorular yanıtlanır — sitenin kendi formunu
    otomatik okumaya çalışmak yerine (kırılgan, login arkası, güvensiz) kullanıcı
    gördüğü soruları bize getiriyor, biz anında cevaplıyoruz.
    Başarısız olursa boş liste döner (çağıran taraf bunu kritik saymamalı)."""
    safe_cv = _sanitize_prompt_text(cv_text)
    safe_desc = _sanitize_prompt_text(job_description)

    if custom_questions:
        numbered = "\n".join(f"{i + 1}. {q.strip()}" for i, q in enumerate(custom_questions[:10]) if q.strip())
        questions_block = f"""Şu soruları, aynı sırayla, ilana ve CV'ye özel somut detaylar içeren 2-4 cümlelik
cevaplar üret (genel geçer/klişe cevap verme). Bu sorular kullanıcının gerçek
başvuru formundan alındı, cevapları buna göre yaz:
{numbered}"""
    else:
        questions_block = """Şu sorulara, aynı sırayla, ilana ve CV'ye özel somut detaylar içeren 2-4 cümlelik
cevaplar üret (genel geçer/klişe cevap verme):
1. Neden bu pozisyona / bu şirkete başvuruyorsunuz?
2. Güçlü yönleriniz nelerdir?
3. Gelişime açık yönleriniz nelerdir?
4. Bu pozisyon için sizi diğer adaylardan ayıran nedir?
5. Ne zaman işe başlayabilirsiniz?"""

    prompt = f"""Sen bir kariyer danışmanısın. Aşağıdaki adayın CV'sine ve ilana göre,
iş başvuru formlarında karşılaşılan sorulara kopyala-yapıştıra hazır,
kişiselleştirilmiş Türkçe cevaplar üret.

Aday: {user_name} — {university}, {department}
Şirket: {company_name}
Pozisyon: {job_title}
İlan Detayı: {safe_desc}
Adayın CV'si: {safe_cv}

{questions_block}

Yanıtı SADECE şu JSON formatında ver:
{{"answers": [{{"question": "...", "answer": "..."}}]}}"""

    try:
        data = await _call_model_async_json(prompt, timeout_seconds=30, api_key=api_key)
        answers = data.get("answers", [])
        return answers if isinstance(answers, list) else []
    except Exception as e:
        logger.error(f"Başvuru soru-cevapları üretilemedi: {type(e).__name__} - {e}")
        return []


async def generate_cold_email(
    company_name: str,
    cv_text: str,
    user_name: str,
    university: str,
    department: str,
    api_key: Optional[str] = None,
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
        client = _get_client(api_key)
        response = await asyncio.wait_for(
            client.aio.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt),
            timeout=30,
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
    api_key: Optional[str] = None,
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
        client = _get_client(api_key)
        response = await asyncio.wait_for(
            client.aio.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt),
            timeout=30,
        )
        return response.text.strip()

    except asyncio.TimeoutError:
        logger.error("CV content generation timeout")
        raise KariyerTimeoutError("CV generation timed out")

    except Exception as e:
        logger.error(f"CV içeriği üretilemedi: {type(e).__name__} - {e}")
        return "[Hata] Özgeçmiş üretilirken API limitlerine takıldık veya sunucu yanıt vermedi."
