import requests
import logging
from typing import List, Dict
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArbeitnowScraper:
    def __init__(self):
        self.api_url = "https://www.arbeitnow.com/api/job-board-api"
        # Senin uzmanlık alanın olan MIS ve Python odaklı anahtar kelimeler
        self.keywords = [
            "management information systems", "mis", 
            "python", "flask", "intern", "staj", 
            "data", "business analyst", "yönetim bilişim",
            "developer", "software"
        ]

    def scrape_jobs(self, limit: int = 50) -> List[Dict]:
        """Arbeitnow API'sinden ilanları çeker ve MIS/Python/Stajyer kriterlerine göre filtreler."""
        logger.info("[Scraper] Arbeitnow API taraması başlıyor...")
        jobs = []
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', [])
                filtered_data = self.filter_jobs(data)
                
                logger.info(f"[Scraper] Arbeitnow API'den {len(data)} ilan çekildi, {len(filtered_data)} tanesi kriterlere uydu.")
                
                for item in filtered_data[:limit]:
                    # Arbeitnow API yanıtını Kariyer Ajanı standart veri yapısına dönüştür
                    title = item.get('title', '')
                    
                    # Staj kelimesini başlıktan sezgisel olarak anlama
                    job_type = "staj" if "intern" in title.lower() or "staj" in title.lower() else "iş"
                    
                    jobs.append({
                        "title": title,
                        "company": item.get('company_name', ''),
                        "location": item.get('location', 'Global'),
                        "source_url": item.get('url', ''),
                        "description": item.get('description', '')[:3000], # Açıklamanın ilk 3000 karakterini al
                        "source": "arbeitnow",
                        "status": "new",
                        "job_type": job_type,
                        "scraped_at": datetime.now(timezone.utc)
                    })
            else:
                logger.error(f"[Scraper] Arbeitnow API isteği başarısız oldu: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"[Scraper] Arbeitnow scraper çalışırken hata oluştu: {e}")
            
        return jobs

    def filter_jobs(self, raw_jobs: List[Dict]) -> List[Dict]:
        """Gelen ham ilanları MIS ve Python odaklı anahtar kelimelerle akıllı şekilde filtreler."""
        uygunlar = []
        for ilan in raw_jobs:
            title = ilan.get('title', '').lower()
            description = ilan.get('description', '').lower()
            
            # Başlıkta veya açıklamada herhangi bir anahtar kelime geçiyorsa listeye dahil et
            if any(key in title for key in self.keywords) or any(key in description for key in self.keywords):
                uygunlar.append(ilan)
                
        return uygunlar

# Modülü bağımsız olarak test etmek istersen aşağıdaki kod bloğu çalışacaktır.
if __name__ == "__main__":
    motor = ArbeitnowScraper()
    ilanlar = motor.scrape_jobs(limit=5)
    for ilan in ilanlar:
        print(f"- {ilan['title']} at {ilan['company']} ({ilan['location']})")
