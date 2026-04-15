from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.api.google_books_client import GoogleBooksClient
from src.api.ndl_client import NdlClient


NDL_XML_RESPONSE = """\
<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcndl="http://ndl.go.jp/dcndl/terms/">
  <numberOfRecords>1</numberOfRecords>
  <records>
    <record>
      <recordSchema>dcndl</recordSchema>
      <recordData>
        <dc:title>方法序説</dc:title>
        <dc:creator>ルネ・デカルト</dc:creator>
        <dc:publisher>岩波書店</dc:publisher>
        <dc:date>1997</dc:date>
        <dc:subject>哲学</dc:subject>
      </recordData>
    </record>
  </records>
</searchRetrieveResponse>
"""

GOOGLE_JSON_RESPONSE = {
    "totalItems": 1,
    "items": [
        {
            "volumeInfo": {
                "title": "吾輩は猫である",
                "authors": ["夏目漱石"],
                "publisher": "岩波書店",
                "publishedDate": "2004",
                "categories": ["小説"],
            }
        }
    ],
}


class TestNdlClient:
    def _mock_response(self, text: str):
        resp = MagicMock()
        resp.text = text
        resp.raise_for_status = MagicMock()
        return resp

    def test_fetch_success(self):
        client = NdlClient()
        with patch.object(client, "_request_with_retry", return_value=self._mock_response(NDL_XML_RESPONSE)):
            book = client.fetch_by_isbn("9784000229819")
        assert book is not None
        assert book.title == "方法序説"
        assert book.author == "ルネ・デカルト"
        assert book.publisher == "岩波書店"
        assert book.published_year == 1997

    def test_fetch_returns_none_on_no_response(self):
        client = NdlClient()
        with patch.object(client, "_request_with_retry", return_value=None):
            book = client.fetch_by_isbn("9784000229819")
        assert book is None

    def test_fetch_returns_none_on_empty_result(self):
        client = NdlClient()
        empty_xml = '<?xml version="1.0"?><searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"><numberOfRecords>0</numberOfRecords><records/></searchRetrieveResponse>'
        with patch.object(client, "_request_with_retry", return_value=self._mock_response(empty_xml)):
            book = client.fetch_by_isbn("9999999999999")
        assert book is None


class TestGoogleBooksClient:
    def _mock_response(self, data: dict):
        resp = MagicMock()
        resp.json.return_value = data
        resp.raise_for_status = MagicMock()
        return resp

    def test_fetch_success(self):
        client = GoogleBooksClient(api_key="test_key")
        with patch.object(client, "_request_with_retry", return_value=self._mock_response(GOOGLE_JSON_RESPONSE)):
            book = client.fetch_by_isbn("9784003101803")
        assert book is not None
        assert book.title == "吾輩は猫である"
        assert book.author == "夏目漱石"
        assert book.published_year == 2004

    def test_fetch_returns_none_on_no_response(self):
        client = GoogleBooksClient()
        with patch.object(client, "_request_with_retry", return_value=None):
            book = client.fetch_by_isbn("9784003101803")
        assert book is None

    def test_fetch_returns_none_on_no_items(self):
        client = GoogleBooksClient()
        with patch.object(client, "_request_with_retry", return_value=self._mock_response({"totalItems": 0})):
            book = client.fetch_by_isbn("9999999999999")
        assert book is None
