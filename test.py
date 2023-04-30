url = 'https://www.dresslily.com/halloween-wolf-print-long-sleeves-product8160053.html'
request = scrapy.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36'})
fetch(request)

response.xpath('.//*[contains(@class,"xxkkk20")]/.').get()