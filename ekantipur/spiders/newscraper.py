import scrapy
import json
import re


class NewscraperSpider(scrapy.Spider):
    name = "newscraper"
    allowed_domains = ["ekantipur.com"]
    # not needed in this case
    # start_urls = ["https://ekantipur.com/photo_feature/2023/12/13?json=true"]

    # news categories
    categories = ["business", "news", "opinion",
                  "sports", "national", "entertainment", "feature", "world", "blog", "koseli", "diaspora", "Education", "photo_feature"]

    # send muliple request for multiple categories
    def start_requests(self):
        for indv_category in self.categories:
            yield scrapy.Request(f"https://ekantipur.com/{indv_category}/2023/12/15?json=true", callback=self.parse)

    # helper function: extracts date using regex
    def extract_date(self, text):
        date_pattern = re.compile(r'प्रकाशित : (.*?) (\d{2}:\d{2})')
        match = date_pattern.search(text)
        if match:
            date = match.group(1)
            return date

    # helper function: extracts author name using regex
    def extract_author(self, text):
        author_pattern = re.compile(r'तस्बिर : (.*)')
        match = author_pattern.search(text)
        if match:
            author = match.group(1)
            return author
        else:
            return text

    def parse(self, response):

        data = json.loads(response.body)

        # pattern for href
        href_pattern = re.compile(r'<h2><a href="(.*?)">')

        # find above pattern from response's json data
        href_matches = href_pattern.findall(data['html'])

        # send request to matched links, pass link as meta to access it inside parse_news function
        for indv_href_match in href_matches:
            yield response.follow(indv_href_match, callback=self.parse_news, meta={'link': indv_href_match})

    def parse_news(self, response):
        # separate parsing for photo_feature category
        if 'photo_feature' in response.meta['link']:

            # initilize empty paragraphs and empty images array to append data later
            paragraphs = []
            images = []

            # access the link variable passed via meta from parse function above
            link = response.meta['link']

            # parse the page to extract relevant data
            title = response.css('div.article-header h1::text').get()
            summary = response.css('div.description p::text').extract_first()
            details = response.css(
                'div.description p:nth-child(n+2)::text')
            image = response.css(
                'div.description div.image img::attr(data-src)')
            author = response.css('span.author a::text').get()
            author_link = response.css('span.author a::attr(href)').get()
            published_date = response.css('span.published-at::text').get()

            for indv_p in details:
                paragraphs.append(indv_p.get())

            for indv_i in image:
                images.append(indv_i.get())

            yield {
                'link': link,
                'title': title,
                'summary': summary,
                'paragraphs': paragraphs,
                'images': images,
                'author': self.extract_author(author),
                'author_link': author_link,
                'published_date': self.extract_date(published_date),
            }

        # parsing for rest of the category
        else:
            # initilize empty paragraphs array and images array to append data later
            paragraphs = []
            images = []

            # access the link variable passed via meta from parse function above
            link = response.meta['link']

            # parse the page to extract relevant data
            title = response.css('div.article-header h1::text').get()
            summary = response.css(
                'div.description.current-news-block p::text').extract_first()
            published_date = response.css('span.published-at::text').get()
            details = response.css(
                'div.description.current-news-block p:nth-child(n+2)::text')
            main_image = response.css(
                'div.description.current-news-block div.image figure img::attr(data-src)').get()
            rest_image = response.css(
                'div.description.current-news-block p img::attr(src)')
            author = response.css('span.author a::text').get()
            author_link = response.css('span.author a::attr(href)').get()

            for indv_p in details:
                paragraphs.append(indv_p.get())

            # append main image

            images.append(main_image)

            # if there are more than one image append them too
            if rest_image:
                for indv_i in rest_image:
                    images.append(indv_i.get())

            yield {
                'link': link,
                'title': title,
                'summary': summary,
                'paragraphs': paragraphs,
                'image': images,
                'author': self.extract_author(author),
                'author_link': author_link,
                "published_date": self.extract_date(published_date)
            }
