# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo
from scrapy.exceptions import DropItem


class MongoPipeline:
    collection_name = "decisions_raw"

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DATABASE")
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection = self.db[self.collection_name]
        self.collection.create_index("partition_date")

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        """
        Process a scraped item and insert it into the MongoDB collection.

        This method attempts to insert the item into the MongoDB collection.
        If the item already exists (duplicate `_id`), it raises a Scrapy `DropItem`
        exception to skip it.
        """
        try:
            self.collection.insert_one(dict(item))
            return item
        except pymongo.errors.DuplicateKeyError:
            raise DropItem(f"Duplicate item found: {item['_id']}")
