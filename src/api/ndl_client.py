from __future__ import annotations

import xml.etree.ElementTree as ET

from src.api.base_client import BaseApiClient
from src.models.book import Book

_NDL_URL = "https://ndlsearch.ndl.go.jp/api/sru"

_NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcndl": "http://ndl.go.jp/dcndl/terms/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}


def _text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    return element.text.strip() if element.text else None


class NdlClient(BaseApiClient):
    def fetch_by_isbn(self, isbn: str) -> Book | None:
        params = {
            "operation": "searchRetrieve",
            "version": "1.2",
            "recordSchema": "dcndl",
            "query": f'isbn="{isbn}"',
            "maximumRecords": "1",
        }
        resp = self._request_with_retry(_NDL_URL, params)
        if resp is None:
            return None

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError:
            return None

        record = root.find(".//srw:recordData", _NS)
        if record is None:
            return None

        title = _text(record.find(".//dc:title", _NS))
        if not title:
            return None

        author_el = record.find(".//dc:creator", _NS)
        publisher_el = record.find(".//dc:publisher", _NS)
        date_el = record.find(".//dc:date", _NS)
        subject_el = record.find(".//dc:subject", _NS)

        year: int | None = None
        if date_el is not None and date_el.text:
            try:
                year = int(date_el.text.strip()[:4])
            except ValueError:
                pass

        return Book(
            isbn=isbn,
            title=title,
            author=_text(author_el),
            publisher=_text(publisher_el),
            published_year=year,
            genre=_text(subject_el),
        )
