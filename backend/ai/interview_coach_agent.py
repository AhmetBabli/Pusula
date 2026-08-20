"""
Kariyer Ajanı 2.0 — Interview Coach Agent
Şirkete, pozisyona ve adayın bölümüne özel mülakat sorusu üretimi + cevap
değerlendirmesi. Şirketin mülakat tarzı/kültürü statik bir tablodan değil,
Gemini'nin Google Search grounding'i ile canlı araştırılarak belirlenir
(bkz. web_search_agent.py — aynı desen).
"""
import asyncio
import json
import logging
import re
from typing import Literal, Optional
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from backend.config import settings
from backend.exceptions import AIServiceError

logger = logging.getLogger("InterviewCoachAgent")


def _get_client(api_key: Optional[str] = None) -> genai.Client:
    return genai.Client(api_key=api_key or settings.GEMINI_API_KEY)


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


async def _generate_grounded_json_with_retry(client: genai.Client, prompt: str, log_prefix: str) -> list:
    """Google Search grounding ile üretir — grounding aktifken
    response_mime_type=json kullanılamadığı için (bkz. web_search_agent.py)
    yanıt metninden JSON dizisini regex ile ayıklar. Ayıklama başarısız
    olursa sessizce boş liste dönüp mülakatı "0 soru" ile kırmak yerine
    AIServiceError fırlatır."""
    config = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
    for attempt in range(3):
        try:
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL, contents=prompt, config=config,
            )
            text = (response.text or "").strip()
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if not match:
                raise AIServiceError("Mülakat soruları üretilemedi (AI yanıtı ayrıştırılamadı).")
            return json.loads(match.group())
        except genai_errors.ServerError as e:
            if attempt < 2:
                logger.warning(f"[{log_prefix}] Gemini geçici olarak meşgul (deneme {attempt + 1}/3), tekrar deneniyor: {e}")
                await asyncio.sleep(2 * (attempt + 1))
                continue
            logger.error(f"[{log_prefix}] Gemini API sürekli meşgul, vazgeçildi: {e}")
            raise AIServiceError(f"AI service temporarily unavailable: {e}")
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"[{log_prefix}] Gemini API çağrısında hata: {type(e).__name__} - {e}")
            raise AIServiceError(f"AI service error: {e}")


# Gemini kotası/API'si geçici olarak kullanılamadığında düşülecek genel yedek
# sorular — şirkete/bölüme özel değildir ama mülakat pratiğini tamamen
# durdurmak yerine kullanıcının en azından pratik yapabilmesini sağlar.
# Çağıran uç (routers/agents.py) bunu kullandığını "personalized: false" ile
# açıkça belirtir, sahte bir "şirkete özel" izlenimi vermez.
FALLBACK_QUESTIONS: list[dict] = [
    {"id": 1, "question": "Kendinizi ve bu pozisyona neden uygun olduğunuzu kısaca anlatır mısınız?", "type": "hr", "hint": "Net, ilgili deneyim/beceriye değinen kısa bir özet."},
    {"id": 2, "question": "Üzerinde çalıştığınız bir projeden bahseder misiniz? Karşılaştığınız en büyük zorluk neydi ve nasıl çözdünüz?", "type": "technical", "hint": "Somut bir proje, karşılaşılan problem, çözüm süreci, sonuç."},
    {"id": 3, "question": "Bir takım içinde fikir ayrılığı yaşadığınız bir durumu nasıl yönettiniz?", "type": "hr", "hint": "Empati, iletişim, çözüm odaklılık."},
    {"id": 4, "question": "Bu alanda kendinizi geliştirmek için hangi kaynakları/yöntemleri kullanıyorsunuz?", "type": "hr", "hint": "Öğrenme isteği, güncel kalma çabası, somut örnek."},
    {"id": 5, "question": "Bu pozisyonda başarılı olmak için en önemli teknik beceri sizce nedir ve bu konudaki seviyenizi nasıl değerlendirirsiniz?", "type": "technical", "hint": "Öz farkındalık, somut örnek, dürüstlük."},
    {"id": 6, "question": "Zaman baskısı altında öncelik belirlemeniz gereken bir durumu nasıl ele aldınız?", "type": "technical", "hint": "Planlama, önceliklendirme mantığı, sonuç."},
]


def get_fallback_questions(round_type: Literal["technical", "hr", "mixed"] = "mixed") -> list[dict]:
    """Şirkete/bölüme özel araştırma yapılamadığında kullanılacak genel sorular."""
    if round_type == "mixed":
        return list(FALLBACK_QUESTIONS)
    filtered = [q for q in FALLBACK_QUESTIONS if q["type"] == round_type]
    return filtered or list(FALLBACK_QUESTIONS)


async def generate_questions(
    job_title: str,
    job_description: str,
    company_name: str,
    round_type: Literal["technical", "hr", "mixed"] = "mixed",
    count: Optional[int] = None,
    user_context: str = "",
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    Google Search grounding ile "{company_name}" hakkında canlı araştırma yapıp
    (sektör, teknoloji yığını, mülakat tarzı/kültürü) + pozisyona + adayın
    bölümüne özel mülakat soruları üretir. Soru sayısı sabit değildir —
    count verilmezse Gemini pozisyonun karmaşıklığına göre kendisi karar verir.
    Returns: [{"id": 1, "question": "...", "type": "technical|hr", "hint": "..."}]
    """
    type_instruction = {
        "technical": "Sadece teknik/mesleki sorular üret.",
        "hr": "Sadece IK/davranışsal sorular üret.",
        "mixed": "Teknik ve IK sorularının dengeli bir karışımını üret.",
    }[round_type]

    count_instruction = (
        f"Tam olarak {count} soru üret."
        if count
        else "Kaç soru gerektiğine kendin karar ver — pozisyonun ve şirketin mülakat "
             "tarzının karmaşıklığına göre genelde 4 ile 8 arasında olur; kıdemli veya "
             "çok yönlü roller için daha fazla, basit/stajyer rolleri için daha az olabilir."
    )

    prompt = f"""Sen deneyimli bir mülakatçısın ve "{company_name}" şirketinin mülakat sürecine
hazırlanıyorsun.

Önce Google'ı kullanarak "{company_name}" hakkında araştırma yap: sektörü, ürün/hizmetleri,
bilinen teknoloji yığını, mülakat süreci/tarzı (varsa Glassdoor, LinkedIn, mülakat deneyimi
paylaşımlarından) ve şirket kültürü/değerleri. Şirket küçük veya az bilinen bir şirketse ve
güvenilir bilgi bulamıyorsan, sektörüne ve pozisyona dayanarak makul bir yaklaşım belirle —
bulamadığın spesifik detayları uydurma.

Pozisyon: {job_title}
İlan Özeti: {job_description[:500]}

{user_context}

Soruları hem POZİSYONA hem de adayın BÖLÜMÜNE/eğitim geçmişine göre uyarla — aynı ilana
başvuran farklı bölümlerden iki aday (örn. Bilgisayar Mühendisliği ile Endüstri Mühendisliği)
çok farklı teknik derinlikte sorular almalı. Mümkün olduğunda şirketin gerçek teknoloji
yığınına/sektörüne ve adayın CV'sindeki/becerilerindeki somut noktalara atıfta bulun
(örneğin "CV'nizde belirttiğiniz X yeteneği" diyerek).

{type_instruction}
{count_instruction}

Her soru için şu alanları içeren bir JSON dizisi üret:
[
  {{
    "id": 1,
    "question": "Soru metni",
    "type": "technical" veya "hr",
    "hint": "İyi bir cevabın içermesi gereken anahtar noktalar (gizli, kullanıcıya gösterilmez)"
  }}
]

Yanıtını SADECE bu JSON dizisi olarak ver, başka açıklama ekleme."""

    client = _get_client(api_key)
    questions = await _generate_grounded_json_with_retry(client, prompt, "InterviewCoach")
    logger.info(f"[InterviewCoach] {len(questions)} soru üretildi (şirket: {company_name}).")
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
