import scrapy
import re
from ..items import Product_Item
from scrapy_splash import SplashRequest

## Script that wait for dynamic element (js) loaded
lua_script = '''
    function main(splash)
      splash:set_user_agent(splash.args.ua)
      assert(splash:go(splash.args.url))
    
      -- requires Splash 2.3  
      while not splash:select('[class*="off js-dl-cutoff"][style*="display: inline-block;"]')  do
        splash:wait(0.5)
        print('loading...')
      end
      return {html=splash:html()}
    end
'''

class HoodieSpiderSpider(scrapy.Spider):

    name = "hoodie_spider"

    custom_settings = {
        'ITEM_PIPELINES': {
           "hoodie_scrape.pipelines.ProductScrapePipeline": 300,
        }
    }

    ## Request first page with splash
    def start_requests(self):
        url = 'https://www.dresslily.com/hoodies-c-181.html'
        yield SplashRequest(url, callback=self.parse)

    ## Processing page
    def parse(self, response):
        ## Collect all product links
        for link in response.xpath('//*[contains(@class,"category-good-name")]/a/@href').getall():
            ## Follow link with splash
            yield SplashRequest(response.urljoin(link), callback=self.product_info_collect, endpoint='execute',
                                args={'lua_source': lua_script,
                                      'ua': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36"},
                                meta={'original_url': link},
                                )
        ## Link to next page
        next_page = response.xpath('.//*[contains(@class,"next-page")]/a/@href').get()
        ## Follow next page
        if next_page is not None:
            next_page_url = 'https://www.dresslily.com' + next_page
            yield response.follow(next_page_url, callback=self.parse)

    def product_info_collect(self, response):
        ## Product info
        product_item = Product_Item()
        product_item["product_id"] = re.search(r"(product)(\d{5,7})", response.meta['original_url']).group(2)
        product_item["product_url"] = response.meta['original_url']
        product_item["name"] = response.xpath('//*[@id="js_goodDetailPage"]/div/div[5]/div[2]/div[2]/h1/span[2]/text()').get()
        product_item["discount"] = response.xpath('.//*[contains(@class, "off js-dl-cutoff")]/span/text()').get()
        product_item["discounted_price"] = response.xpath('.//*[contains(@class,"dl-price")]/text()').get()
        product_item["original_price"] = response.xpath('.//*[contains(@class,"dl-price")]/text()').get()
        product_item["total_reviews"] = response.xpath('.//*[contains(@class,"review-all-count js-goreview")]/a/text()').get()
        product_item["product_info"] = "".join(
            re.findall(
                r'\>(.*?)\<' ,
                response.xpath('.//*[contains(@class,"xxkkk20")]/.').get()\
                    .replace('\n', '') \
                    .replace('<strong>', ';') \
                    .replace(' ', ''),
                flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE
            )
        )

        # yield { "page_url" : response.meta['original_url'] }
        yield product_item
