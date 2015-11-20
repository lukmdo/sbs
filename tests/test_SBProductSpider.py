# -*- coding: utf-8 -*-
import pytest

from sbs import SBProductSpider


@pytest.fixture(scope="module")
def spider():
    return SBProductSpider()


def test_parse(spider, product_page):
    parsed_item = spider.parse(page=product_page)
    assert parsed_item.title == 'PRODUCT TITLE'
    assert parsed_item.description == 'PRODUCT DESCRIPTION'
    assert parsed_item.price == 20.3
    assert parsed_item.size == '38.5kb'


def test_parse_with_utf8(spider, utf8_product_page):
    parsed_item = spider.parse(page=utf8_product_page)
    assert parsed_item.title == 'PRODUCT♡ TITLE ∑'
    assert parsed_item.description == 'PRODUCT DESCRIPTION ♡♡♡'


def test_parse_malformed(spider, malformed_product_page):
    parsed_item = spider.parse(page=malformed_product_page)
    assert parsed_item.title == ''
    assert parsed_item.description == ''
    assert parsed_item.price == 0


def test_dict_item(spider):
    item = spider.Item(
        title='TITLE', description='DESCRIPTION', price=20.1, size='20.5kb')
    data = spider.dict_item(item)
    assert data == dict(
        title='TITLE', description='DESCRIPTION', price=20.1, size='20.5kb')
