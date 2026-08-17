from urllib.parse import urldefrag, urljoin, urlparse
from scrapling.spiders import Request, Response, Spider

TARGET = "https://devaito.com/"
HOSTS = {"devaito.com", "www.devaito.com"}
SKIP = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".pdf", ".zip",
    ".mp4", ".mp3", ".css", ".js", ".xml", ".json", ".woff", ".woff2", ".ttf"
)


def clean_url(base, href):
    href = (href or "").strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None

    url, _ = urldefrag(urljoin(base, href))
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or parsed.hostname not in HOSTS:
        return None
    if parsed.path.lower().endswith(SKIP):
        return None

    return url


class DevaitoSpider(Spider):
    name = "devaito"
    start_urls = [TARGET]
    concurrent_requests = 4
    robots_txt_obey = True
    autothrottle_enabled = True

    async def parse(self, response: Response):
        links = sorted({
            url
            for href in response.css("a::attr(href)").getall()
            if (url := clean_url(response.url, href))
        })

        yield {
            "url": response.url,
            "status": response.status,
            "title": response.css("title::text").get(),
            "meta_description": response.css('meta[name="description"]::attr(content)').get(),
            "meta_robots": response.css('meta[name="robots"]::attr(content)').get(),
            "canonical": response.css('link[rel="canonical"]::attr(href)').get(),
            "lang": response.css("html::attr(lang)").get(),
            "h1": response.css("h1::text").getall(),
            "h2": response.css("h2::text").getall(),
            "h3": response.css("h3::text").getall(),
            "paragraphs": response.css("p::text").getall(),
            "buttons": response.css("button::text").getall(),
            "internal_links": links,
            "json_ld": response.css('script[type="application/ld+json"]::text').getall(),
            "og_title": response.css('meta[property="og:title"]::attr(content)').get(),
            "og_description": response.css('meta[property="og:description"]::attr(content)').get(),
        }

        for url in links:
            yield Request(url, callback=self.parse)


if __name__ == "__main__":
    result = DevaitoSpider(crawldir="./crawl_data/devaito").start()
    result.items.to_json("devaito-scrape.json")
    print(f"Scraped {len(result.items)} pages -> devaito-scrape.json")
