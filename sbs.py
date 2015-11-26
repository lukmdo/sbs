#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Assumptions:
- ok to break execution if any of product fetching fails (all or nothing)
- ok to add extra logging to Stderr
- ok to skip nice help and options (otherwise would use http://click.pocoo.org/)
- ok with Very basic tests
- ok with python>=3.4
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


VERSION = (0, 0, 2)
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
REQ_TIMEOUT_SEC = 5
ERROR_CODE_TIMEOUT = 2
ERROR_CODE_CONNECTION = 3
ERROR_CODE_RESPONSE = 4

log = logging.getLogger(__name__)


def main():
    # Setup logging
    default_log_handler = logging.StreamHandler()
    default_log_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'))
    log.setLevel(logging.INFO)
    log.addHandler(default_log_handler)

    page = get_main_page()
    spider = SBSpider()
    item = spider.parse(page=page)
    data = spider.dict_item(item)

    print(json.dumps(data, sort_keys=True, indent=2))


def _fetch_page(url, timeout=REQ_TIMEOUT_SEC):
    """
    :rtype requests.Response
    :raises
    will sys.exit on error with code
    - requests.exceptions.HTTPError
    - ERROR_CODE_TIMEOUT
    - ERROR_CODE_CONNECTION
    """
    msg = 'Fetching {}'.format(url)
    log.info(msg)
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        log.exception(msg + ' - Response NOT 200 OK')
        exit(ERROR_CODE_RESPONSE)
    except requests.exceptions.Timeout:
        log.exception(msg + ' - Timeout')
        exit(ERROR_CODE_TIMEOUT)
    except requests.exceptions.ConnectionError:
        log.exception(msg + ' - Connection Failure')
        exit(ERROR_CODE_CONNECTION)

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
    return page


class Spider(object):
    # `parse` and `pare_document` should return self.Item
    Item = collections.namedtuple('Item', [])

    parser = lxml.html.HTMLParser(compact=False)

    @staticmethod
    def dict_item(self, item):
        """
        Convert `item` to dict
        """
        raise NotImplementedError

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
        'Item', ('title', 'unit_price', 'description', 'size'))

    @staticmethod
    def dict_item(item):
        return vars(item)

    class Selectors(object):
        @staticmethod
        def title(document):
            element = CSSSelector(
                '.productTitleDescriptionContainer > h1')(document)
            if not element:
                return ''
            element = element[0]
            text = element.text_content().strip()
            return text

        @staticmethod
        def price(document):
            element = CSSSelector('.productSummary .pricePerUnit')(document)
            if not element:
                return 0
            element = element[0]
            match = SBProductSpider.price_regx.search(element.text_content())
            price = float(match.group(0)) if match else 0
            return price

        @staticmethod
        def description(document):
            element = CSSSelector('#information .productText')(document)
            if not element:
                return ''
            element = element[0]
            text = element.text_content().strip()
            if text.startswith('Description'):
                text = text[11:].lstrip()
            return text

    def parse_document(self, document, raw):
        title = self.Selectors.title(document)
        price = self.Selectors.price(document)
        description = self.Selectors.description(document)
        size = '{:.01f}kb'.format(len(raw) / 1024)  # http 'Content-Length'

        return self.Item(
            title=title, unit_price=price, description=description, size=size)


class SBSpider(Spider):
    """
    Main Sainsbury's Shop Page Spider
    """
    item_spider = SBProductSpider()
    Item = collections.namedtuple('Item', ('results', 'total'))

    @staticmethod
    def dict_item(item):
        return {
            'results': [
                SBProductSpider.dict_item(item) for item in item.results],
            'total': item.total,
        }

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
            total += result.unit_price

        return self.Item(results=results, total=total)


if __name__ == '__main__':
    main()
