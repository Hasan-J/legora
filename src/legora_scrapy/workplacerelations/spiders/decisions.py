from dateutil.parser import parse as dateparse
from scrapy import Request, Spider


class DecisionsSpider(Spider):
    name = "decisions"
    allowed_domains = ["workplacerelations.ie"]

    # spider args
    page = 1
    query = None
    from_date = None
    to_date = None
    body = None
    partition_date = None

    async def start(self):
        """
        Construct the search URL for decisions and yield an initial request.

        This method builds query parameters based on the attributes of the instance,
        formats dates, and includes optional filtering criteria. It then constructs
        the full search URL and yields a Scrapy Request.

        Attributes Used:
            query (str, optional): Search string to filter decisions.
            from_date (str, optional): Start date in a format parsable by `dateparse`.
            to_date (str, optional): End date in a format parsable by `dateparse`.
            body (str, optional): Filter code(s) for specific tribunals.
                Body codes:
                1      Equality Tribunal
                2      Employment Appeals Tribunal
                3      Labour Court
                15376  Workplace Relations Commission

                Note: Omitting `body` will scrape data from all tribunals by default.

        Yields:
            scrapy.Request: Initial request to the search page with constructed query.
        """
        params = {"decisions": 1}
        if self.query:
            params["q"] = f"“{self.query}”"
        if self.from_date:
            params["from"] = dateparse(self.from_date).strftime("%-d/%-m/%Y")
        if self.to_date:
            params["to"] = dateparse(self.to_date).strftime("%-d/%-m/%Y")
        if self.body:
            params["body"] = self.body

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"https://workplacerelations.ie/en/search/?{query_string}"
        self.log(f"Sart URL: {url}")
        self.log(f"Params: {params}")
        yield Request(url)

    def parse(self, response):
        for case in response.css("div.item-list.search-list li.each-item"):
            link = response.urljoin(case.css("h2.title a::attr(href)").get())
            decision_id = case.css("h2.title a::text").get()
            if decision_id:
                yield {
                    "_id": decision_id,
                    "link": link,
                    "date": case.css("span.date::text").get(),
                    "ref_no": case.css("span.refNO::text").get(),
                    "parties": case.css("p.description::text").get(),
                    "partition_date": self.partition_date,
                    "file_urls": [link],
                }
            else:
                self.log(
                    f"Decision Id element not found for case {case}, skipping.")

        next_page = response.css(
            "div.ptools-pager ul.pager li a.next::attr(href)").get()

        if next_page:
            self.log(f"Found next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)
