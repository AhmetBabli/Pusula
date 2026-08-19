"""
Kariyer Ajanı 2.0 — Web Search Agent
Gemini Grounding ile canlı iş ilanı ve şirket haberi araması.
"""
import asyncio
import logging
from typing import Optional
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from backend.config import settings
from backend.exceptions import AIServiceError

logger = logging.getLogger("WebSearchAgent")


def _get_client(api_key: Optional[str] = None) -> genai.Client:
    return genai.Client(api_key=api_key or settings.GEMINI_API_KEY)


async def _generate_with_retry(client: genai.Client, prompt: str, log_prefix: str):
    """Gemini'nin geçici 'high demand' (503) yanıtları için kısa aralıklarla en
    fazla 2 kez daha dener. Denemeler tükenince sessizce boş liste dönüp
    'aranan hiçbir şey bulunamadı' izlenimi vermek yerine AIServiceError
    fırlatır — çağıran background task bunu push_agent_event(..., 'failed', ...)
    ile arayüze doğru şekilde yansıtır."""
    for attempt in range(3):
        try:
            return await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL, contents=prompt, config=_grounding_config()
            )
        except genai_errors.ServerError as e:
            if attempt < 2:
                logger.warning(f"[{log_prefix}] Gemini geçici olarak meşgul (deneme {attempt + 1}/3), tekrar deneniyor: {e}")
                await asyncio.sleep(2 * (attempt + 1))
                continue
            logger.error(f"[{log_prefix}] Gemini API sürekli meşgul, vazgeçildi: {e}")
            raise AIServiceError(f"AI service temporarily unavailable: {e}")


def _grounding_config() -> types.GenerateContentConfig:
    """Google Search grounding aktif üretim konfigürasyonu döner."""
    return types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )


async def search_jobs_live(query: str, location: str = "Türkiye", api_key: Optional[str] = None) -> list[dict]:
    """
    Gemini Grounding ile gerçek zamanlı iş/staj ilanı arar.
    Döndürülen liste ScrapedJobContract uyumlu dict'lerdir.
    """
    prompt = f"""
Sen bir kariyer danışmanısın. Google'ı kullanarak şu an için açık olan iş ilanlarını bul.

Arama sorgusu: "{query}" — Lokasyon: {location}

Bulduğun her ilan için şu bilgileri çıkar:
- title: İlanın pozisyon adı
- company: Şirket adı
- location: Ofis lokasyonu
- source_url: İlanın URL'si (varsa)
- description: Kısa açıklama (max 300 karakter)
- job_type: "staj" veya "tam_zamanlı"

Yanıtı SADECE şu JSON dizisi formatında ver, başka açıklama ekleme:
[{{"title":"...","company":"...","location":"...","source_url":"...","description":"...","job_type":"..."}}]
"""
    client = _get_client(api_key)
    response = await _generate_with_retry(client, prompt, "WebSearch")

    import json, re
    text = (response.text or "").strip()
    # JSON bloğunu ayıkla — grounding aktifken response_mime_type=json kullanılamıyor,
    # bu yüzden serbest metin içinden diziyi regex ile çekiyoruz.
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        logger.warning(f"[WebSearch] Gemini yanıtında JSON dizisi bulunamadı: {text[:200]!r}")
        return []

    jobs = json.loads(match.group())
    for j in jobs:
        j.setdefault("source", "gemini_grounding")
        j.setdefault("status", "new")
    logger.info(f"[WebSearch] Gemini Grounding → {len(jobs)} ilan bulundu.")
    return jobs


async def get_company_news(company_name: str, api_key: Optional[str] = None) -> list[dict]:
    """Şirket hakkında son haberleri çeker."""
    prompt = f"""
"{company_name}" şirketi hakkında son 30 günlük haberleri bul.
Özellikle: işe alım, büyüme, yeni ürünler, kariyer haberleri.

JSON formatında döndür:
[{{"headline":"...","summary":"...","date":"YYYY-MM-DD","url":"..."}}]
"""
    client = _get_client(api_key)
    response = await _generate_with_retry(client, prompt, "WebSearch")

    import json, re
    text = (response.text or "").strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        logger.warning(f"[WebSearch] Şirket haberleri yanıtında JSON dizisi bulunamadı: {text[:200]!r}")
        return []
    return json.loads(match.group())
