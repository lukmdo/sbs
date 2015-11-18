#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TODO: add assumptions
"""
import re
import io
import json
import logging
import collections

import lxml.etree
import lxml.html
from lxml.cssselect import CSSSelector
import requests
import requests.exceptions


VERSION = (0, 0, 1)
__version__ = VERSION
__versionstr__ = '.'.join(map(str, VERSION))

URL = (
    'http://www.sainsburys.co.uk'
    '/webapp/wcs/stores/servlet/AjaxApplyFilterBrowseView'
    '?msg=&langId=44&categoryId=185749&storeId=10151'
    '&krypto=W4nD444s6eTWJa2gf91udgghPhw3b48DueW9z9C4cnnOIMY5lk2f8r2GwJkiLr9iA'
    'b6lUlJf3Z%2Bp%0ACbUBNmcotDEywy54CRfpDBxKGpCOHp0qvA68nVo29OoLis1UW4CV8kdc1'
    'IcoVeZxUZ%2FuBmFSJ5Jz%0Ah9rsDZkPn%2F9zErvK22TJAvNb1vE0m8LtWh9YyBAgBe73rpz'
    '7NM2llRHxiP02PJWQ0nDeyt324Taz%0AaMuK3%2FovR2uKRbx0vHMOi2EwHSef'
    '&ddkey=http:AjaxApplyFilterBrowseView')
_REQ_TIMEOUT_SEC = 5
log = logging.getLogger(__name__)


def main():
    # Setup logging
    default_log_handler = logging.StreamHandler()
    default_log_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'))
    log.setLevel(logging.INFO)
    log.addHandler(default_log_handler)

    page = get_main_page()
    result = SBSpider().parse(page=page)
    data = {
        'results': [vars(item) for item in result.results],
        'total': result.total,
    }
    print(json.dumps(data, sort_keys=True, indent=2))


def _fetch_page(url, timeout=_REQ_TIMEOUT_SEC):
    """
    :rtype requests.Response
    """
    msg = 'Fetching {}'.format(url)
    log.info(msg)
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        log.error(msg + ' - Timeout')
    log.info(msg + ' - Done')

    return resp


def get_main_page():
    page = _fetch_page(URL)
    page_data = page.json()
    items = []
    for doc in page_data:
        if 'productLists' in doc:
            products = doc['productLists'][0]['products']
            items = [item['result'] for item in products]
            break

    page = '\n'.join(items)
    return  page

class Spider(object):
    # `parse` and `pare_document` should return Item
    Item = collections.namedtuple('Item', [])

    parser = lxml.html.HTMLParser(compact=False)
    # remove_comments=False
    # remove_pis=False
    # strip_cdata=False

    class Selectors(object):
        """
        Groups selectors for readability and some perf
        """
    def from_url(self, url):
        resp = _fetch_page(url)
        document = self.from_page(resp.text)
        return document, resp

    def from_page(self, page):
        """
        :type page:
        :rtype:
        """
        return lxml.html.parse(io.StringIO(page), parser=self.parser)

    def parse(self, url=None, page=None):
        if url:
           document, resp = self.from_url(url)
           page = resp.text
        elif page:
           document = self.from_page(page)

        return self.parse_document(document, page)

    def parse_document(self, document, raw):
        """
        :type document:
        :type Spider.Item
        """
        raise NotImplementedError


class SBProductSpider(Spider):
    """
    Sainsbury's Shop Product Page Spider
    """
    price_regx = re.compile('(\d+(:?\.\d+)?)')
    Item = collections.namedtuple(
        'Item', ('title', 'price', 'description', 'size'))

    class Selectors(object):
        @staticmethod
        def title(document):
            return CSSSelector(
                '.productTitleDescriptionContainer > h1')(document)[0].text

        @staticmethod
        def price(document):
            element = CSSSelector('.productSummary .pricePerUnit')(document)[0]
            match = SBProductSpider.price_regx.search(element.text_content())
            price = float(match.group(0)) if match else 0
            return price

        @staticmethod
        def description(document):
            element = CSSSelector('#information .productText')(document)[0]
            text = element.text_content().strip()
            if text.startswith('Description'):
                text = text[11:].lstrip()
            return text

    def parse_document(self, document, raw):
        title = self.Selectors.title(document)
        price = self.Selectors.price(document)
        description = self.Selectors.description(document)
        size = '{:.01f}kb'.format(len(raw) / 1024)

        return self.Item(
            title=title, price=price, description=description, size=size)


class SBSpider(Spider):
    """
    Main Sainsbury's Shop Page Spider
    """
    item_spider = SBProductSpider()
    Item = collections.namedtuple('Item', ('results', 'total'))

    class Selectors(object):
        @staticmethod
        def items(document):
            return CSSSelector('.productInfo a')(document)

    def parse_document(self, document, raw):
        results = []
        total = 0
        for link in self.Selectors.items(document):
            result = self.item_spider.parse(url=link.get('href'))
            results.append(result)
            total += result.price

        return self.Item(results=results, total=total)


if __name__ == '__main__':
    main()
