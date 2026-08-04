"""
Kariyer Ajanı 2.0 — Web Search Agent
Gemini Grounding ile canlı iş ilanı ve şirket haberi araması.
"""
import logging
from typing import Optional
import google.generativeai as genai
from backend.config import settings

logger = logging.getLogger("WebSearchAgent")

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


def _grounding_model():
    """Google Search grounding aktif Gemini modeli döner."""
    tool = genai.protos.Tool(
        google_search=genai.protos.GoogleSearch()
    )
    return genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        tools=[tool],
    )


async def search_jobs_live(query: str, location: str = "Türkiye") -> list[dict]:
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
        model = _grounding_model()
        response = await model.generate_content_async(prompt)
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


async def get_company_news(company_name: str) -> list[dict]:
    """Şirket hakkında son haberleri çeker."""
    prompt = f"""
"{company_name}" şirketi hakkında son 30 günlük haberleri bul.
Özellikle: işe alım, büyüme, yeni ürünler, kariyer haberleri.

JSON formatında döndür:
[{{"headline":"...","summary":"...","date":"YYYY-MM-DD","url":"..."}}]
"""
    try:
        model = _grounding_model()
        response = await model.generate_content_async(prompt)
        import json, re
        text = response.text.strip()
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        logger.error(f"[WebSearch] Şirket haberleri alınamadı: {e}")
    return []
