# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ProductScrapePipeline:
    def process_item(self, item, spider):

        adapter = ItemAdapter(item)
        adapter.field_names()

        # discounted_price rule
        if adapter.get('discount') is None:
            adapter['discounted_price'] = 0
        else:
            None

        # original price
        def calculate_original(discount, discounted_price, original_price):
            if discount:
                original = float(discounted_price) + (float(discounted_price) * 0.01 * float(discount))
                return round(original, 3)
            else:
                return original_price

        adapter['original_price'] = calculate_original(discount=adapter.get('discount'),
                                                       discounted_price=adapter.get('discounted_price'),
                                                       original_price=adapter.get('original_price'))

        if adapter['total_reviews'] is None:
            adapter['total_reviews'] == None
        else:
            adapter['total_reviews'] = adapter.get('total_reviews')[1:]


        return item
