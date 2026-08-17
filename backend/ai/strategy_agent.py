"""
Kariyer Ajanı 2.0 — Oracle Career Strategist Agent
Mevcut profil vs Hedef pozisyon analizi + 6 aylık yol haritası.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from backend.config import settings

logger = logging.getLogger("StrategyAgent")

async def generate_career_strategy(
    current_skills: List[str],
    current_title: str,
    target_job: str,
    target_location: str = "Global",
    github_analysis: str = "",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Kullanıcı için stratejik yol haritası ve pazar analizi üretir.
    """
    prompt = f"""Sen bir 'Executive Career Strategist' ve 'Market Intelligence' uzmanısın.
Kullanıcının mevcut durumunu analiz edip, hayalindeki pozisyona ulaşması için nokta atışı bir strateji belirle.

MEVCUT DURUM:
- Ünvan: {current_title}
- Yetenekler: {', '.join(current_skills)}
- GitHub Analizi: {github_analysis[:1000]}

HEDEF:
- Pozisyon: {target_job}
- Lokasyon: {target_location}

Lütfen şu formatta JSON döndür:
{{
  "market_overview": {{
    "salary_range": "Maaş skalası (Örn: £60k - £90k)",
    "demand_level": "Talep yoğunluğu (Yüksek/Orta/Düşük)",
    "top_technologies": ["Trend teknoloji 1", "2", "3"]
  }},
  "skill_gap_analysis": [
    {{ "skill": "Yetenek adı", "importance": "Kritik/Önemli", "reason": "Neden gerekli?" }}
  ],
  "roadmap_6_months": [
    {{ "month": "1-2", "focus": "Odaklanılacak konu", "actions": ["Aksiyon 1", "Aksiyon 2"] }},
    {{ "month": "3-4", "focus": "Odaklanılacak konu", "actions": ["Aksiyon 1", "Aksiyon 2"] }},
    {{ "month": "5-6", "focus": "Odaklanılacak konu", "actions": ["Aksiyon 1", "Aksiyon 2"] }}
  ],
  "project_ideas": [
    {{ "title": "Proje adı", "description": "Neden bu proje seni öne çıkarır?" }}
  ],
  "final_advice": "Kısa ve vurucu bir kapanış tavsiyesi."
}}

SADECE JSON döndür."""

    try:
        client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"[StrategyAgent] Hata: {e}")
        return {
            "market_overview": {"salary_range": "Veri alınamadı", "demand_level": "Bilinmiyor", "top_technologies": []},
            "skill_gap_analysis": [],
            "roadmap_6_months": [],
            "project_ideas": [],
            "final_advice": "Strateji şu an oluşturulamıyor."
        }
