import json
import logging
from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field, ValidationError
from backend.ai.gemini_client import _get_model  # require_json parametresini desteklediğini varsayıyoruz

# Loglama yapılandırması
logger = logging.getLogger("EmailIntelligenceAgent")

# --- Pydantic Modelleri (Veri Doğrulama İçin) ---
class EmailOpportunity(BaseModel):
    """Gemini'den dönecek JSON formatının kesin şeması"""
    type: Literal["job", "event", "hackathon", "career_fair", "course", "update", "junk"]
    title: str = Field(default="Fırsat Tespiti")
    company: str = Field(default="Bilinmeyen")
    summary: str = Field(default="İçerik özeti çıkarılamadı.")
    deadline: Optional[str] = None
    action_required: str = Field(default="İnceleme gerekiyor")
    relevance_score: int = Field(ge=0, le=100) # 0 ile 100 arasında olmasını garanti eder


class EmailIntelligenceAgent:
    """
    Agent responsible for extracting 'Career Intelligence' from emails.
    Powered by Gemini AI.
    """

    @staticmethod
    async def process_email(subject: str, sender: str, body: str) -> Optional[Dict]:
        """
        Processes a raw/cleaned email to find career opportunities.
        Returns None if the email is junk/irrelevant.
        """
        # Gövdeyi güvenli uzunluğa kırp
        safe_body = body.strip()[:2000] if body else ""
        
        prompt = f"""Bir Kariyer İstihbarat Uzmanısın. Aşağıdaki e-postayı analiz et ve eğer kariyerle ilgili bir fırsat (staj, iş ilanı, eğitim, hackathon, fuar vb.) içeriyorsa detaylarını ayıkla.

İçerik Kariyerle ilgili değilse 'type' alanını 'junk' olarak işaretle.

E-posta Detayları:
Gönderen: {sender}
Konu: {subject}
İçerik:
{safe_body}

Aşağıdaki şemaya tam olarak uyan SADECE geçerli bir JSON döndür:
{{
    "type": "job" | "event" | "hackathon" | "career_fair" | "course" | "update" | "junk",
    "title": "<ilgi çekici kısa başlık>",
    "company": "<şirket adı veya organizatör>",
    "summary": "<deftere yazılacak kısa, samimi ve profesyonel özet. Staj/iş ilanıysa belirt.>",
    "deadline": "<varsa YYYY-MM-DD, yoksa null>",
    "action_required": "<kullanıcının yapması gereken eylem>",
    "relevance_score": <0-100 arası ilgi puanı>
}}"""

        try:
            # Önceki refactor'da eklediğimiz require_json=True özelliği kullanılıyor
            model = _get_model(require_json=True)
            
            # Asenkron çağrı (Event loop bloklanmaz)
            response = await model.generate_content_async(prompt)
            
            if not response or not hasattr(response, "text"):
                raise ValueError("Modelden geçerli bir yanıt dönmedi.")

            # JSON Parsing ve Pydantic Validation
            raw_dict = json.loads(response.text)
            validated_data = EmailOpportunity.model_validate(raw_dict)
            
            # Junk veya düşük skor kontrolü
            if validated_data.type == "junk" or validated_data.relevance_score < 20:
                logger.info(f"E-posta elendi (Score: {validated_data.relevance_score}, Type: {validated_data.type}) -> {subject}")
                return None
                
            # Dictionary olarak dışarı aktar
            return validated_data.model_dump()
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Gemini çıktısı doğrulanamadı veya JSON formatında değildi: {e}")
            return EmailIntelligenceAgent._fallback_heuristic(subject, sender, safe_body)
            
        except Exception as e:
            logger.error(f"Email AI processing error: {e}")
            return EmailIntelligenceAgent._fallback_heuristic(subject, sender, safe_body)

    @staticmethod
    def _fallback_heuristic(subject: str, sender: str, body: str) -> Optional[Dict]:
        """AI başarısız olduğunda çalışacak yedek algoritma (Heuristic Fallback)"""
        text_lower = (subject + " " + body).lower()
        career_keywords = ["staj", "iş ilanı", "kariyer", "mülakat", "başvuru", "teklif", "hackathon", "etkinlik", "yetenek"]
        
        if any(k in text_lower for k in career_keywords):
            # Fallback durumunda da veriyi Pydantic modelinden geçirerek formatı garantiye alıyoruz
            try:
                fallback_data = EmailOpportunity(
                    type="update",
                    title=subject[:100],
                    company=sender.split("@")[0] if "@" in sender else sender,
                    summary="AI analizi yapılamadı ancak e-posta kariyerle ilgili görünüyor. Lütfen manuel kontrol edin.",
                    deadline=None,
                    action_required="E-postayı manuel oku",
                    relevance_score=60
                )
                return fallback_data.model_dump()
            except ValidationError:
                pass # Çok absürt bir sender string'i gelirse hata vermesini engelle
                
        return None