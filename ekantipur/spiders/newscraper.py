import scrapy
import json
import re
from datetime import datetime, timedelta
from config import categories, start_date_str, end_date_str


class NewscraperSpider(scrapy.Spider):
    name = "newscraper"
    allowed_domains = ["ekantipur.com"]

    # convert date string into date objects
    start_date = datetime.strptime(start_date_str, "%Y/%m/%d")
    end_date = datetime.strptime(end_date_str, "%Y/%m/%d")
    current_date = start_date

    # read the data file
    try:
        with open('kantipur_news.json', 'r', encoding='utf-8') as file:
            data_list = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        data_list = []

    # start request by looping through each date and each category, pass date as meta to access it later

    def start_requests(self):
        while self.current_date <= self.end_date:
            for indv_category in categories:
                yield scrapy.Request("https://ekantipur.com/{}/{}?json=true".format(indv_category, self.current_date.strftime("%Y/%m/%d")), callback=self.parse, meta={'news_date': self.current_date.strftime("%Y/%m/%d"), 'news_category': indv_category})

            self.current_date += timedelta(days=1)

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

        news_date = response.meta['news_date']
        news_category = response.meta['news_category']
        # find above pattern from response's json data
        href_matches = href_pattern.findall(data['html'])

        # send request to matched links, pass link as meta to access it inside parse_news function
        for indv_href_match in href_matches:
            # check for duplicates
            found = any(item['link'] ==
                        indv_href_match for item in self.data_list)
            if not found:
                yield response.follow(indv_href_match, callback=self.parse_news, meta={'link': indv_href_match, 'news_date': news_date, 'news_category': news_category})

    def parse_news(self, response):
        # separate parsing for photo_feature category
        if 'photo_feature' in response.meta['link']:

            # initilize empty paragraphs and empty images array to append data later
            paragraphs = []
            images = []

            # access the link variable passed via meta from parse function above
            link = response.meta['link']
            news_date = response.meta['news_date']
            news_category = response.meta['news_category']
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

            scraped_data = {
                'news_date': news_date,
                'published_date': self.extract_date(published_date),
                'news_category': news_category.capitalize(),
                'link': link,
                'title': title,
                'summary': summary,
                'paragraphs': paragraphs,
                'images': images,
                'author': self.extract_author(author),
                'author_link': author_link

            }
            self.data_list.append(scraped_data)

            yield scraped_data

        # parsing for rest of the category
        else:
            # initilize empty paragraphs array and images array to append data later
            paragraphs = []
            images = []

            # access the link variable and news_date passed via meta from parse function above
            link = response.meta['link']
            news_date = response.meta['news_date']
            news_category = response.meta['news_category']

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

            scraped_data = {
                'news_date': news_date,
                'published_date': self.extract_date(published_date),
                'news_category': news_category.capitalize(),
                'link': link,
                'title': title,
                'summary': summary,
                'paragraphs': paragraphs,
                'image': images,
                'author': self.extract_author(author),
                'author_link': author_link

            }
            self.data_list.append(scraped_data)

            yield scraped_data

    # write data
    def closed(self, reason):
        with open('kantipur_news.json', 'w', encoding='utf-8') as json_file:
            json.dump(self.data_list, json_file, ensure_ascii=False, indent=4)
