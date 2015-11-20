from unittest.mock import create_autospec

import pytest
import requests


@pytest.fixture
def response_mock():
    """
    requests.Response mock
    """
    return create_autospec(requests.Response)


@pytest.fixture(scope="session")
def products_page():
    """
    Multi products list page content.
    """
    with open('data/products.html') as f:
        return ''.join(f)


@pytest.fixture(scope="session")
def product_page():
    """
    Single product page content.
    """
    with open('data/product.html') as f:
        return ''.join(f)


@pytest.fixture(scope="session")
def utf8_product_page():
    """
    Single product page with utf8 content.
    """
    with open('data/product_utf8.html') as f:
        return ''.join(f)


@pytest.fixture(scope="session")
def malformed_product_page():
    """
    Single product page with malformed content.

    See <!-- BROKEN HTML: THIS SHOULD BE HERE --> in data/product_malformed.html
    """
    with open('data/product_malformed.html') as f:
        return ''.join(f)
