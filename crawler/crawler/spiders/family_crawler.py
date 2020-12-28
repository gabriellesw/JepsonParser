import scrapy
from config import Config


class JepsonFamilyCrawler(scrapy.Spider):
    name = "family"
    start_urls = [Config().CRAWLER_START_URL]

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = f'quotes-{page}.html'
        with open(filename, 'wb') as f:
            f.write(response.body)