# -*- coding: utf-8 -*-
from unittest.mock import ANY, patch, call

import pytest
import requests

from sbs import SBSpider


@pytest.fixture(scope="module")
def spider():
    return SBSpider()


def test_parse(spider, products_page, product_page, response_mock, ):
    responses = [response_mock(), response_mock()]
    responses[0].text = product_page
    responses[1].text = product_page

    with patch.object(requests, 'get') as mocked_get:
        mocked_get.side_effect = responses
        parsed_item = spider.parse(page=products_page)

        calls = mocked_get.mock_calls
        assert call('PRODUCT_1_URL', timeout=ANY) in calls
        assert call('PRODUCT_1_URL', timeout=ANY) in calls
        assert len(calls) == 2

    assert len(parsed_item.results) == 2
    assert parsed_item.total == 40.6

    data = spider.dict_item(parsed_item)
    assert data['total'] == 40.6
    assert len(data['results']) == 2


def test_dict_item(spider):
    item = spider.Item(results=[], total=0)
    data = spider.dict_item(item)
    assert data == dict(results=[], total=0)
