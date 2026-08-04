import logging
import time
import random
from typing import List, Dict
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInScraper:
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search"

    def scrape_jobs(self, query: str = "Yönetim Bilişim Sistemleri staj", limit: int = 15) -> List[Dict]:
        """LinkedIn üzerinden ilanları çeker (Girişsiz/Guest flow)."""
        jobs = []
        browser = None  # finally bloğunda güvenli kapatmak için

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1366, "height": 768},
                    locale="tr-TR"
                )
                page = context.new_page()
                target_url = f"{self.base_url}?keywords={query}&location=Turkey&f_TPR=r604800&f_JT=I"

                logger.info(f"[Scraper] LinkedIn taraması başlıyor: {query}")
                page.goto(target_url, wait_until="domcontentloaded")
                time.sleep(random.uniform(3.0, 5.0))

                desc_page = context.new_page()

                job_cards = (
                    page.query_selector_all(".base-card") or
                    page.query_selector_all(".job-search-card") or
                    page.query_selector_all(".jobs-search-results__list-item") or
                    page.query_selector_all(".result-card")
                )

                logger.info(f"[Scraper] Bulunan ilan kartı sayısı (LinkedIn): {len(job_cards)}")

                for card in job_cards[:limit]:
                    try:
                        title_elem = card.query_selector(".base-search-card__title")
                        company_elem = card.query_selector(".base-search-card__subtitle")
                        link_elem = card.query_selector("a.base-card__full-link")

                        if title_elem and company_elem and link_elem:
                            title = title_elem.inner_text().strip()
                            company = company_elem.inner_text().strip()
                            url = link_elem.get_attribute("href").split("?")[0]

                            sleep_time = random.uniform(2.5, 4.5)
                            time.sleep(sleep_time)

                            description = ""
                            try:
                                desc_page.goto(url, wait_until="domcontentloaded", timeout=15000)
                                time.sleep(random.uniform(1.0, 2.0))
                                desc_elem = (
                                    desc_page.query_selector('.show-more-less-html__markup') or
                                    desc_page.query_selector('.description__text')
                                )
                                if desc_elem:
                                    description = desc_elem.inner_text().strip()[:3000]
                                else:
                                    logger.warning(f"[Scraper] LinkedIn login duvarı olabilir: {url}")
                            except Exception as e:
                                logger.warning(f"[Scraper] LinkedIn detay çekilemedi ({url}): {e}")

                            # job_type normalize
                            raw_type = "staj" if "staj" in title.lower() or "intern" in title.lower() else "tam_zamanlı"

                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": "Türkiye",
                                "source_url": url,
                                "description": description,
                                "source": "linkedin",
                                "status": "new",
                                "job_type": raw_type,
                                "scraped_at": datetime.now(timezone.utc)
                            })
                    except Exception as e:
                        logger.error(f"[Scraper] LinkedIn kartı ayrıştırılırken hata: {e}")

                desc_page.close()
                logger.info(f"[OK] LinkedIn'den başarıyla {len(jobs)} ilan çekildi.")

        except Exception as e:
            logger.error(f"[Scraper] LinkedIn scraper kökten çöktü: {e}")
        finally:
            # Browser her durumda kapat — bellek sızıntısını önler
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

        return jobs