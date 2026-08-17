"""
Kariyer Ajanı 2.0 — Web Search Agent
Gemini Grounding ile canlı iş ilanı ve şirket haberi araması.
"""
import logging
from typing import Optional
from google import genai
from google.genai import types
from backend.config import settings

logger = logging.getLogger("WebSearchAgent")


def _get_client(api_key: Optional[str] = None) -> genai.Client:
    return genai.Client(api_key=api_key or settings.GEMINI_API_KEY)


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
    try:
        client = _get_client(api_key)
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL, contents=prompt, config=_grounding_config()
        )
        import json, re
        text = response.text.strip()
        # JSON bloğunu ayıkla
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            jobs = json.loads(match.group())
            # source alanını ekle
            for j in jobs:
                j.setdefault("source", "gemini_grounding")
                j.setdefault("status", "new")
            logger.info(f"[WebSearch] Gemini Grounding → {len(jobs)} ilan bulundu.")
            return jobs
    except Exception as e:
        logger.error(f"[WebSearch] Gemini Grounding hatası: {e}")
    return []


async def get_company_news(company_name: str, api_key: Optional[str] = None) -> list[dict]:
    """Şirket hakkında son haberleri çeker."""
    prompt = f"""
"{company_name}" şirketi hakkında son 30 günlük haberleri bul.
Özellikle: işe alım, büyüme, yeni ürünler, kariyer haberleri.

JSON formatında döndür:
[{{"headline":"...","summary":"...","date":"YYYY-MM-DD","url":"..."}}]
"""
    try:
        client = _get_client(api_key)
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL, contents=prompt, config=_grounding_config()
        )
        import json, re
        text = response.text.strip()
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        logger.error(f"[WebSearch] Şirket haberleri alınamadı: {e}")
    return []
