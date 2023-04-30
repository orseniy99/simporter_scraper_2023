import warnings
warnings.filterwarnings("ignore")

import scrapy
import re
from ..items import Review_Item
from scrapy_splash import SplashRequest
from scrapy.selector import Selector

from datetime import datetime
import time

## Script that wait for dynamic element (js) loaded
lua_script_load_comments = '''
    function main(splash)
      splash:set_user_agent(splash.args.ua)
      assert(splash:go(splash.args.url))
      
      while not splash:select('[class*="site-pager good-site-pager"]')  do
        splash:wait(0.5)
        print('loading pagination...')
      end
      
      return {html=splash:html()}
    end
'''

lua_script_reviews_next_page = '''
    function main(splash)
      splash:set_user_agent(splash.args.ua)
      assert(splash:go(splash.args.url))
      
      if splash:select('#js_reviewPager > ul > li:nth-of-type(11) > a > svg') then
        local next_page_button = splash:select('#js_reviewPager > ul > li:nth-of-type(11) > a > svg')
        button:mouse_click()
      end
      
      splash:wait(1.5)
      
      return {html=splash:html()}
    end
'''

class ReviewsSpiderSpider(scrapy.Spider):
    name = "reviews_spider"

    # custom_settings = {
    #     'ITEM_PIPELINES': {
    #         "hoodie_scrape.pipelines.ProductScrapePipeline": 300,
    #     }
    # }

    def start_requests(self):
        url = 'https://www.dresslily.com/hoodies-c-181.html'
        yield SplashRequest(url, callback=self.parse)

    def parse(self, response):
        ## Collect all product links
        for link in response.xpath('//*[contains(@class,"category-good-name")]/a/@href').getall():
            yield SplashRequest(response.urljoin(link), callback=self.collect_product_reviews,
                                # endpoint='execute',
                                # args={'lua_source': lua_script_load_comments,
                                #       'ua': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36"},
                                meta={'original_url': link},
                                )

        ## Link to next page
        next_page = response.xpath('.//*[contains(@class,"next-page")]/a/@href').get()
        ## Follow next page
        if next_page is not None:
            next_page_url = 'https://www.dresslily.com' + next_page
            yield response.follow(next_page_url, callback=self.parse)

    def collect_product_reviews(self, response):
        link = response.meta['original_url']

        def datetime_str_to_unix(str):
            unix = time.mktime(datetime.strptime(str, "%b,%d %Y %H:%M:%S").timetuple())
            return int(unix)

        if response.xpath('.//*[contains(@class, "good-reviewinfo")]'):

            # reviews_count = response.xpath('.//*[contains(@id, "js_reviewCountText")]/text()').get()
            # print(f"Find {reviews_count} reviews for: {link}")

            for review in response.xpath('.//*[contains(@class,"reviewinfo table")]'):
                review_item = Review_Item()

                review_item["product_id"] = re.search(r"(product)(\d{5,7})", link).group(2)

                review_item["rating"] = len(Selector(text=review.extract()).xpath(
                    './/*[contains(@class, "review-star")]/i').getall())

                review_item["timestamp"] = datetime_str_to_unix(Selector(text=review.extract()).xpath(
                    './/*[contains(@class, "review-time")]/text()').get())

                review_item["text"] = Selector(text=review.extract()).xpath(
                    './/*[contains(@class, "review-content-text")]/text()').get()

                review_item["size"] = Selector(text=review.extract()).xpath(
                    './/*[contains(@class, "review-good-size")]/span/text()').getall()[-2]

                review_item["color"] = Selector(text=review.extract()).xpath(
                    './/*[contains(@class, "review-good-size")]/span/text()').getall()[-1]

                # print(Selector(text=review.extract()).xpath('.//*[contains(@class, "review-content-text")]/text()').extract())

                yield review_item

                yield SplashRequest(link, callback=self.collect_product_reviews, endpoint='execute',
                                    args={'lua_source': lua_script_reviews_next_page,
                                          'ua': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36"},
                                    meta={'original_url': link},
                                    )


        else:
            print(f'No reviews for {link}')
            yield None
