import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ScraperTest")

from backend.scrapers.arbeitnow_scraper import ArbeitnowScraper
from backend.scrapers.youthall_scraper import YouthallScraper
from backend.scrapers.kariyer_net_scraper import KariyerNetScraper
from backend.scrapers.linkedin_scraper import LinkedInScraper

async def test_all_scrapers():
    logger.info("Starting Scrapers Diagnostic...")
    
    # 1. Test Arbeitnow
    logger.info("--- Testing Arbeitnow Scraper ---")
    try:
        arbeitnow = ArbeitnowScraper()
        jobs = arbeitnow.scrape_jobs(limit=3)
        logger.info(f"Arbeitnow found {len(jobs)} jobs.")
        for j in jobs:
            logger.info(f" - [Arbeitnow] {j['title']} at {j['company']}")
    except Exception as e:
        logger.error(f"Arbeitnow failed: {e}", exc_info=True)

    # 2. Test Youthall
    logger.info("--- Testing Youthall Scraper ---")
    try:
        youthall = YouthallScraper()
        jobs = youthall.scrape_jobs(limit=3, query="staj")
        logger.info(f"Youthall found {len(jobs)} jobs.")
        for j in jobs:
            logger.info(f" - [Youthall] {j['title']} at {j['company']}")
    except Exception as e:
        logger.error(f"Youthall failed: {e}", exc_info=True)

    # 3. Test Kariyer.net (Playwright)
    logger.info("--- Testing Kariyer.net Scraper ---")
    try:
        kariyer = KariyerNetScraper()
        jobs = await kariyer.scrape_jobs(query="staj", limit=3)
        logger.info(f"Kariyer.net found {len(jobs)} jobs.")
        for j in jobs:
            logger.info(f" - [Kariyer.net] {j['title']} at {j['company']}")
    except Exception as e:
        logger.error(f"Kariyer.net failed: {e}", exc_info=True)

    # 4. Test LinkedIn (Playwright)
    logger.info("--- Testing LinkedIn Scraper ---")
    try:
        linkedin = LinkedInScraper()
        jobs = await asyncio.to_thread(linkedin.scrape_jobs, query="staj", limit=3)
        logger.info(f"LinkedIn found {len(jobs)} jobs.")
        for j in jobs:
            logger.info(f" - [LinkedIn] {j['title']} at {j['company']}")
    except Exception as e:
        logger.error(f"LinkedIn failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_all_scrapers())
