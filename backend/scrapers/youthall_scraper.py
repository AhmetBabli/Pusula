import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouthallScraper:
    """
    Youthall Scraper: Fetches internship and job listings from youthall.com
    """
    BASE_URL = "https://www.youthall.com"
    JOBS_URL = "https://www.youthall.com/tr/is-ilanlari/"

    def __init__(self):
        # Oturum (Session) kullanımı: Çerezleri tutarak banlanma riskini azaltır
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/" # Google'dan geliyormuş gibi göster
        })

    def _tag_text_by_icon(self, card, icon_class: str) -> str:
        """`.jobs-tag` öğeleri arasından belirli bir <i> ikon sınıfına sahip olanın metnini döndürür."""
        icon = card.select_one(f"i.{icon_class}")
        if icon and icon.parent:
            return icon.parent.get_text(strip=True)
        return ""

    def _parse_row_card(self, card) -> Dict:
        """`.jobs-row` (liste) düzenindeki kartı ayrıştırır."""
        link_tag = card if card.name == "a" else card.select_one("a.jobs-row__link")
        link = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
        if link and not link.startswith("http"):
            link = self.BASE_URL + link

        title_tag = card.select_one(".jobs-row__title h5")
        title = title_tag.get_text(strip=True) if title_tag else "Bilinmeyen Başlık"

        company_tag = card.select_one(".jobs-row__company")
        company = company_tag.get_text(strip=True) if company_tag else "Bilinmeyen Şirket"

        desc_tag = card.select_one(".jobs-row__desc")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        logo_tag = card.select_one(".jobs-row__logo")
        logo_url = logo_tag["src"] if logo_tag and logo_tag.has_attr("src") else None

        job_type_text = self._tag_text_by_icon(card, "fa-briefcase")
        location = self._tag_text_by_icon(card, "fa-map-marker-alt") or "Türkiye"

        return {
            "source": "youthall",
            "source_url": link,
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "company_logo_url": logo_url,
            "job_type": "staj" if "staj" in (job_type_text or title).lower() else "tam_zamanlı",
            "scraped_at": datetime.now(timezone.utc),
        }

    def _parse_grid_card(self, card) -> Dict:
        """`.jobs` (grid) düzenindeki kartı ayrıştırır — bu düzende ayrı bir şirket adı
        elementi yok, şirket adı logo görselinin alt metninden çıkarılır."""
        link_tag = card if card.name == "a" else card.find("a", recursive=False)
        link = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
        if link and not link.startswith("http"):
            link = self.BASE_URL + link

        title_tag = card.select_one(".jobs-content-title h5")
        title = title_tag.get_text(strip=True) if title_tag else "Bilinmeyen Başlık"

        logo_tag = card.select_one(".jobs-content-logo")
        logo_url = logo_tag["src"] if logo_tag and logo_tag.has_attr("src") else None
        logo_alt = logo_tag["alt"] if logo_tag and logo_tag.has_attr("alt") else ""
        company = logo_alt[:-len(" logo")].strip() if logo_alt.lower().endswith(" logo") else (logo_alt or "Bilinmeyen Şirket")

        desc_tag = card.select_one(".jobs-content-desc")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        job_type_text = self._tag_text_by_icon(card, "fa-briefcase")
        location = self._tag_text_by_icon(card, "fa-map-marker-alt") or "Türkiye"

        return {
            "source": "youthall",
            "source_url": link,
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "company_logo_url": logo_url,
            "job_type": "staj" if "staj" in (job_type_text or title).lower() else "tam_zamanlı",
            "scraped_at": datetime.now(timezone.utc),
        }

    def scrape_jobs(self, limit: int = 30, query: str = "staj") -> List[Dict]:
        """Scrapes the latest jobs from Youthall (hem grid hem liste düzenindeki kartlardan)."""
        logger.info(f"[Scraper] Youthall üzerinden ilanlar taranıyor: {self.JOBS_URL}")

        try:
            response = self.session.get(self.JOBS_URL, timeout=15)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"[Scraper] Youthall ana sayfası çekilemedi: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        row_cards = soup.select(".jobs-row")
        grid_cards = soup.select("div.jobs")
        logger.info(f"[Scraper] Bulunan ilan kartı sayısı (Youthall): {len(row_cards)} liste + {len(grid_cards)} grid")

        job_items: List[Dict] = []
        seen_urls = set()

        for card in row_cards + grid_cards:
            try:
                parsed = self._parse_row_card(card) if "jobs-row" in (card.get("class") or []) else self._parse_grid_card(card)
                if not parsed["source_url"] or parsed["source_url"] in seen_urls:
                    continue
                seen_urls.add(parsed["source_url"])
                job_items.append(parsed)
            except Exception as e:
                logger.warning(f"[Scraper] İlan kartı ayrıştırılırken hata: {e}")
                continue

            if len(job_items) >= limit:
                break

        for item in job_items:
            if item["source_url"]:
                sleep_time = random.uniform(1.0, 2.0)
                time.sleep(sleep_time)
                item["description"] = item["description"] or self._fetch_description(item["source_url"])

        logger.info(f"[OK] Youthall'dan başarıyla {len(job_items)} ilan çekildi.")
        return job_items

    def _fetch_description(self, url: str) -> str:
        """Fetch detailed description from the job page."""
        try:
            req = self.session.get(url, timeout=10)
            req.raise_for_status()
            soup = BeautifulSoup(req.text, 'html.parser')
            desc_div = soup.find('div', class_=lambda x: x and ('description' in x.lower() or 'detail' in x.lower() or 'content' in x.lower()))
            if desc_div:
                return desc_div.get_text(separator=' ', strip=True)[:3000]

            main = soup.find('main') or soup.find('body')
            return main.get_text(separator=' ', strip=True)[:3000] if main else ""
        except Exception as e:
            # Sessizce ölmek yerine en azından hatayı görelim
            logger.warning(f"[Scraper] Detay sayfası çekilemedi ({url}): {e}")
            return ""

if __name__ == "__main__":
    scraper = YouthallScraper()
    jobs = scraper.scrape_jobs(5)
    for j in jobs:
        print(f"- {j['title']} @ {j['company']} ({j['location']}) [{j['job_type']}]")
