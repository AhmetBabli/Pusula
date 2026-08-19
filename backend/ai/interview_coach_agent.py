"""
Kariyer Ajanı 2.0 — Interview Coach Agent
Şirkete özel teknik/IK soru üretimi + cevap değerlendirmesi.
"""
import asyncio
import json
import logging
from typing import Literal, Optional
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from backend.config import settings
from backend.exceptions import AIServiceError

logger = logging.getLogger("InterviewCoachAgent")


async def _generate_json_with_retry(client: genai.Client, prompt: str, log_prefix: str) -> dict | list:
    """Gemini'nin geçici 'high demand' (503) yanıtları için kısa aralıklarla en
    fazla 2 kez daha dener (bkz. gemini_client.py::_call_model_async_json —
    aynı disiplin). Denemeler tükenince sessizce sahte bir sonuca düşmek
    yerine AIServiceError fırlatır: çağıran uç bunu ya global exception
    handler'a (temiz 503 yanıtı) ya da push_agent_event(..., 'failed', ...)'a
    yönlendirip kullanıcıya gerçek durumu gösterir."""
    for attempt in range(3):
        try:
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            return json.loads(response.text)
        except genai_errors.ServerError as e:
            if attempt < 2:
                logger.warning(f"[{log_prefix}] Gemini geçici olarak meşgul (deneme {attempt + 1}/3), tekrar deneniyor: {e}")
                await asyncio.sleep(2 * (attempt + 1))
                continue
            logger.error(f"[{log_prefix}] Gemini API sürekli meşgul, vazgeçildi: {e}")
            raise AIServiceError(f"AI service temporarily unavailable: {e}")
        except Exception as e:
            logger.error(f"[{log_prefix}] Gemini API çağrısında hata: {type(e).__name__} - {e}")
            raise AIServiceError(f"AI service error: {e}")

# Şirket kültürü veritabanı — mülakat ağırlıkları
COMPANY_PROFILES: dict[str, dict] = {
    "baykar": {
        "style": "teknik-ağırlıklı, mühendislik odaklı",
        "focus": ["C/C++", "gömülü sistemler", "algoritma", "matematik", "problem çözme"],
        "hr_style": "milliyetçi değerler, sorumluluk bilinci, disiplin",
    },
    "turkcell": {
        "style": "vaka analizi ağırlıklı, iş odaklı",
        "focus": ["telekomunikasyon", "dijital dönüşüm", "müşteri deneyimi", "ürün yönetimi"],
        "hr_style": "liderlik, inovasyon, müşteri odaklılık",
    },
    "trendyol": {
        "style": "hız, ölçek, veri odaklı",
        "focus": ["sistem tasarımı", "mikroservisler", "veri yapıları", "SQL optimizasyonu"],
        "hr_style": "ownership, büyüme zihniyeti, sonuç odaklılık",
    },
    "default": {
        "style": "dengeli teknik + IK",
        "focus": ["problem çözme", "takım çalışması", "teknoloji", "proje yönetimi"],
        "hr_style": "iletişim, uyum, öğrenme hızı",
    },
}


def _get_company_profile(company_name: str) -> dict:
    key = company_name.lower().strip()
    for k, v in COMPANY_PROFILES.items():
        if k in key:
            return v
    return COMPANY_PROFILES["default"]


async def generate_questions(
    job_title: str,
    job_description: str,
    company_name: str,
    round_type: Literal["technical", "hr", "mixed"] = "mixed",
    count: int = 5,
    user_context: str = "",
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    Şirket kültürüne + ilan içeriğine + adayın profiline uygun mülakat soruları üretir.
    Returns: [{"id": 1, "question": "...", "type": "technical|hr", "hint": "..."}]
    """
    profile = _get_company_profile(company_name)

    type_instruction = {
        "technical": f"Sadece teknik sorular üret. Odak: {', '.join(profile['focus'][:4])}",
        "hr": f"Sadece IK/davranışsal sorular üret. Tarz: {profile['hr_style']}",
        "mixed": f"Karışık: {count//2} teknik, {count - count//2} IK sorusu.",
    }[round_type]

    prompt = f"""Sen deneyimli bir {company_name} mülakatçısısın.
Şirket kültürü: {profile['style']}

Pozisyon: {job_title}
İlan Özeti: {job_description[:500]}

{user_context}

Adayın yeteneklerine ve CV'sine atıfta bulunarak (örneğin "CV'nizde belirttiğiniz X yeteneği" diyerek) soruları kişiselleştirin.
{type_instruction}

Her soru için şu JSON formatını kullan:
[
  {{
    "id": 1,
    "question": "Soru metni",
    "type": "technical" veya "hr",
    "hint": "İyi bir cevabın içermesi gereken anahtar noktalar (gizli, kullanıcıya gösterilmez)"
  }}
]

SADECE JSON döndür, açıklama ekleme. {count} soru üret."""

    client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
    questions = await _generate_json_with_retry(client, prompt, "InterviewCoach")
    logger.info(f"[InterviewCoach] {len(questions)} soru üretildi.")
    return questions


async def evaluate_answer(
    question: str,
    answer: str,
    question_type: str,
    hint: str,
    job_title: str,
    company_name: str,
    api_key: Optional[str] = None,
) -> dict:
    """
    Kullanıcının cevabını değerlendirir.
    Returns: {"score": 75, "feedback": "...", "strengths": [...], "improvements": [...]}
    """
    prompt = f"""Sen bir {company_name} kıdemli mülakatçısısın.

Pozisyon: {job_title}
Soru: {question}
Beklenen anahtar noktalar (dahili): {hint}

Aday Cevabı: {answer[:800]}

Cevabı değerlendir. JSON formatında döndür:
{{
  "score": <0-100 arası puan>,
  "feedback": "<genel değerlendirme, 2-3 cümle>",
  "strengths": ["<güçlü nokta 1>", "<güçlü nokta 2>"],
  "improvements": ["<geliştirme önerisi 1>", "<geliştirme önerisi 2>"],
  "model_answer_hint": "<ideal cevabın içermesi gereken 1-2 anahtar nokta>"
}}"""

    client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
    result = await _generate_json_with_retry(client, prompt, "InterviewCoach")
    result["score"] = max(0, min(100, int(result.get("score", 50))))
    return result
