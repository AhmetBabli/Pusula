"""
Kariyer Ajanı 2.0 — Metin-Konuşma (Text-to-Speech) İstemcisi
Mülakat Koçu'nun sorularını sesli okuması için Google Cloud Text-to-Speech
REST API'sini (basit API anahtarıyla, servis hesabı gerekmeden) kullanır.
"""
import base64
import logging
from typing import Optional

import httpx

from backend.config import settings
from backend.exceptions import AIServiceError

logger = logging.getLogger("TtsClient")

TTS_ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"


async def synthesize_speech(text: str, language_code: str = "tr-TR") -> bytes:
    """Metni MP3 ses verisine çevirir. Uygulama genelinde tek bir anahtar
    kullanılır (kullanıcı bazlı değil) — bkz. settings.GOOGLE_TTS_API_KEY."""
    if not settings.GOOGLE_TTS_API_KEY:
        raise AIServiceError("Sesli okuma şu an yapılandırılmamış (GOOGLE_TTS_API_KEY eksik).")

    if not text or not text.strip():
        raise AIServiceError("Seslendirilecek metin boş.")

    payload = {
        "input": {"text": text[:5000]},  # Google TTS tek istekte ~5000 karakterle sınırlı
        "voice": {"languageCode": language_code, "ssmlGender": "FEMALE"},
        "audioConfig": {"audioEncoding": "MP3"},
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                TTS_ENDPOINT,
                params={"key": settings.GOOGLE_TTS_API_KEY},
                json=payload,
            )
        if response.status_code != 200:
            logger.error(f"[TTS] Google API hatası: {response.status_code} {response.text[:300]}")
            raise AIServiceError(f"Sesli okuma servisi hata döndürdü ({response.status_code}).")

        audio_b64 = response.json().get("audioContent")
        if not audio_b64:
            raise AIServiceError("Sesli okuma servisi ses verisi döndürmedi.")
        return base64.b64decode(audio_b64)

    except httpx.HTTPError as e:
        logger.error(f"[TTS] Ağ hatası: {e}")
        raise AIServiceError(f"Sesli okuma servisine ulaşılamadı: {e}")
