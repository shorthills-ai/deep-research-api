import asyncio
from crawl4ai import AsyncWebCrawler


async def basic_crawler(url,default=None):
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
                extract_text=True,
            )
            if not result.success:
                print(f"Failed to scrape {url}: {result.error}")
                return default
            print(result.markdown[:300])  # Show the first 300 characters of extracted text
            return result.markdown
if __name__ == "__main__":
    asyncio.run(basic_crawler("https://www.linkedin.com/company/oneam-us"))
