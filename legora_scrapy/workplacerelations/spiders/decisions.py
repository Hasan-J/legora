import scrapy


class DecisionsSpider(scrapy.Spider):
    name = "decisions"
    allowed_domains = ["workplacerelations.ie"]
    start_urls = ["https://workplacerelations.ie/en/search/?decisions=1"]

    def parse(self, response):
        pass
