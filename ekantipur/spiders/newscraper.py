import scrapy
import json
import re


class NewscraperSpider(scrapy.Spider):
    name = "newscraper"
    allowed_domains = ["ekantipur.com"]
    # start_urls = ["https://ekantipur.com/photo_feature/2023/12/13?json=true"]
    categories = ["business", "news", "opinion",
                  "sports", "national", "entertainment", "feature", "world", "blog", "koseli", "diaspora", "Education", "photo_feature"]

    def start_requests(self):
        for cat in self.categories:
            yield scrapy.Request(f"https://ekantipur.com/{cat}/2023/12/13?json=true", callback=self.parse)

    def extract_date(self, text):
        date_pattern = re.compile(r'प्रकाशित : (.*?) (\d{2}:\d{2})')
        match = date_pattern.search(text)
        if match:
            date = match.group(1)
            return date

    def parse(self, response):

        data = json.loads(response.body)

        href_pattern = re.compile(r'<h2><a href="(.*?)">')
        href_matches = href_pattern.findall(data['html'])

        for href_match in href_matches:
            yield response.follow(href_match, callback=self.parse_news, meta={'link': href_match})

    def parse_news(self, response):
        if 'photo_feature' in response.meta['link']:

            paragraphs = []
            images = []
            title = response.css('div.article-header h1::text').get()
            summary = response.css('div.description p::text').extract_first()
            link = response.meta['link']
            details = response.css(
                'div.description p:nth-child(n+2)::text')
            image = response.css(
                'div.description div.image img::attr(data-src)')
            author = response.css('span.author a::text').get()
            author_link = response.css('span.author a::attr(href)').get()
            published_date = response.css('span.published-at::text').get()

            for p in details:
                paragraphs.append(p.get())

            for i in image:
                images.append(i.get())

            yield {
                'link': link,
                'title': title,
                'summary': summary,
                'paragraphs': paragraphs,
                'images': images,
                'author': author,
                'author_link': author_link,
                'published_date': self.extract_date(published_date),
            }

        else:
            paragraphs = []
            title = response.css('div.article-header h1::text').get()
            summary = response.css(
                'div.description.current-news-block p::text').extract_first()
            link = response.meta['link']
            published_date = response.css('span.published-at::text').get()
            details = response.css(
                'div.description.current-news-block p:nth-child(n+2)::text')
            image = response.css(
                'div.description.current-news-block div.image figure img::attr(data-src)').get()
            author = response.css('span.author a::text').get()
            author_link = response.css('span.author a::attr(href)').get()

            for p in details:
                paragraphs.append(p.get())

            yield {
                'link': link,
                'title': title,
                'summary': summary,
                'paragraphs': paragraphs,
                'image': image,
                'author': author,
                'author_link': author_link,
                "published_date": self.extract_date(published_date)

            }
