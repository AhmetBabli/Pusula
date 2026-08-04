import logging
import asyncio
import random
from typing import List, Dict
from datetime import datetime, timezone
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperBlockedException(Exception):
    """Captcha, IP ban veya auth-wall durumunda fırlatılır."""
    pass


class KariyerNetScraper:
    def __init__(self):
        self.base_url = "https://www.kariyer.net/is-ilanlari"

    async def scrape_jobs(self, query: str = "Yönetim Bilişim Sistemleri", limit: int = 20) -> List[Dict]:
        """Kariyer.net üzerinden ilanları çeker (async ve anti-bot korumalı)."""
        jobs = []
        browser = None  # finally bloğunda güvenli kapatmak için
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="tr-TR"
                )
                page = await context.new_page()
                target_url = f"{self.base_url}?kw={query}"
                logger.info(f"[Scraper] Kariyer.net taraması başlıyor: {target_url}")

                try:
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    raise ScraperBlockedException(f"Kariyer.net'e erişilemedi (captcha/timeout?): {e}")

                await asyncio.sleep(random.uniform(3.0, 5.0))

                desc_page = await context.new_page()

                job_cards = (
                    await page.query_selector_all('[data-test="ad-card"]') or
                    await page.query_selector_all(".list-items .item") or
                    await page.query_selector_all(".job-card") or
                    await page.query_selector_all(".k-ad-card") or
                    await page.query_selector_all("article")
                )

                logger.info(f"[Scraper] Bulunan ilan kartı sayısı (Kariyer.net): {len(job_cards)}")

                for card in job_cards[:limit]:
                    try:
                        title_elem = await card.query_selector('[data-test="ad-card-title"]') or await card.query_selector(".k-ad-card-title") or await card.query_selector("h3")
                        company_elem = await card.query_selector('[data-test="subtitle"]') or await card.query_selector(".k-ad-card-company") or await card.query_selector(".subtitle")
                        location_elem = await card.query_selector('[data-test="location"]')
                        link_elem = await card.query_selector('[data-test="ad-card-item"]') or await card.query_selector("a")

                        if title_elem and company_elem and link_elem:
                            title = (await title_elem.inner_text()).strip()
                            company = (await company_elem.inner_text()).strip()
                            location = (await location_elem.inner_text()).strip() if location_elem else "Türkiye"
                            href = await link_elem.get_attribute("href")
                            url = href if href.startswith("http") else f"https://www.kariyer.net{href}"

                            # Kart kök elementindeki yapısal veri özniteliği; metin ayrıştırmadan
                            # çok daha güvenilir bir çalışma-tipi kaynağı.
                            work_type_attr = await card.get_attribute("worktypetext")

                            sleep_time = random.uniform(2.0, 4.5)
                            await asyncio.sleep(sleep_time)

                            description = ""
                            try:
                                await desc_page.goto(url, wait_until="domcontentloaded", timeout=15000)
                                await asyncio.sleep(random.uniform(1.0, 2.0))
                                desc_elem = (
                                    await desc_page.query_selector('.job-detail-content') or
                                    await desc_page.query_selector('.job-desc') or
                                    await desc_page.query_selector('main')
                                )
                                if desc_elem:
                                    description = (await desc_elem.inner_text()).strip()[:3000]
                            except Exception as e:
                                logger.warning(f"[Scraper] Kariyer.net açıklama çekilemedi ({url}): {e}")

                            # job_type normalize: yapısal öznitelik varsa onu, yoksa başlığı kullan
                            raw_type = "staj" if "staj" in (work_type_attr or title).lower() else "tam_zamanlı"

                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": location,
                                "source_url": url,
                                "description": description,
                                "source": "kariyer_net",
                                "status": "new",
                                "job_type": raw_type,
                                "scraped_at": datetime.now(timezone.utc)
                            })
                    except Exception as e:
                        logger.error(f"[Scraper] Kariyer.net kartı ayrıştırılırken hata: {e}")

                await desc_page.close()
                logger.info(f"[OK] Kariyer.net'ten başarıyla {len(jobs)} ilan çekildi.")

        except ScraperBlockedException as e:
            logger.warning(f"[BLOCKED] Kariyer.net erişim engeli: {e}")
        except Exception as e:
            logger.error(f"[Scraper] Kariyer.net scraper kökten çöktü: {e}")
        finally:
            # Browser her durumda kapat — bellek sızıntısını önler
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass

        return jobs