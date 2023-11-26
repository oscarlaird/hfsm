import aiohttp
import asyncio
import backoff

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

@backoff.on_exception(backoff.expo,
                      aiohttp.ClientError,
                      max_tries=8)
async def download_url(session, url):
    try:
        html = await fetch(session, url)
        return html
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

async def download_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [download_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Example usage
urls = [
    "https://www.wikipedia.org/",
    "https://www.github.com/",
    "https://www.stackoverflow.com/",
    "https://www.medium.com/",
    "https://www.nasa.gov/",
    "https://www.nature.com/",
    "https://www.bbc.com/news",
    "https://www.cnn.com/",
    "https://www.nytimes.com/",
    "https://www.theguardian.com/international",
    "https://www.forbes.com/",
    "https://www.nationalgeographic.com/"
]

htmls = asyncio.run(download_all(urls))
for url, html in zip(urls, htmls):
    print(f"Downloaded {url}: {len(html)}: {html[:10]}...")
