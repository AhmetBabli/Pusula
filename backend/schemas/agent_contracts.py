"""
Kariyer Ajanı — Ajan Kontrat Şemaları
Tüm scraper'ların dönmesi gereken standart veri formatları.
Pydantic validator'ları ile scraper → DB pipeline'ında şema uyumsuzluklarını önler.
"""
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ScrapedJobContract(BaseModel):
    """
    Tüm Scraper ajanlarının döndürmesi ZORUNLU olan standart kontrat.
    Bu şemadan geçmeyen veri Job() modeline asla ulaşmaz.
    """
    title: str = Field(..., min_length=2, max_length=300)
    company: str = Field(..., min_length=1, max_length=200)
    location: str = Field(default="Türkiye", max_length=200)
    source_url: str = Field(..., min_length=10, max_length=1000)
    description: str = Field(default="")
    requirements: str = Field(default="")
    source: Literal["kariyer_net", "linkedin", "youthall", "arbeitnow"]
    job_type: Literal["staj", "tam_zamanlı", "yarı_zamanlı"] = "tam_zamanlı"
    sector: Optional[str] = None
    company_logo_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("job_type", mode="before")
    @classmethod
    def normalize_job_type(cls, v: str) -> str:
        """
        'iş', 'full-time', 'internship' gibi farklı kaynaklardan gelen
        değerleri standart enum değerlerine dönüştürür.
        """
        mapping = {
            "iş": "tam_zamanlı",
            "is": "tam_zamanlı",
            "full-time": "tam_zamanlı",
            "fulltime": "tam_zamanlı",
            "tam zamanlı": "tam_zamanlı",
            "tam_zamanli": "tam_zamanlı",
            "part-time": "yarı_zamanlı",
            "parttime": "yarı_zamanlı",
            "yarı zamanlı": "yarı_zamanlı",
            "internship": "staj",
            "intern": "staj",
            "staj": "staj",
        }
        return mapping.get(str(v).lower().strip(), "tam_zamanlı")

    @field_validator("source_url", mode="before")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """URL boş veya çok kısa ise reddeder."""
        if not v or len(v.strip()) < 10:
            raise ValueError("source_url geçerli bir URL olmalıdır.")
        return v.strip()

    @field_validator("title", "company", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return str(v).strip() if v else ""

    def to_job_dict(self) -> dict:
        """
        SQLAlchemy Job() modeline doğrudan **kwargs olarak geçirilebilecek
        temiz sözlük döndürür. scraped_at gibi datetime nesneleri korunur.
        """
        return self.model_dump(exclude_none=False)
