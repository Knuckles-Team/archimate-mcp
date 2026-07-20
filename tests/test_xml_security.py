"""Security regression coverage for ArchiMate exchange parsing."""

import pytest

from archimate_mcp.api import xml_security


def test_exchange_parser_rejects_dtd(tmp_path):
    document = tmp_path / "model.xml"
    document.write_text(
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///ignored">]><root>&xxe;</root>',
        encoding="utf-8",
    )
    with pytest.raises(xml_security.ExchangeXmlError, match="invalid"):
        xml_security.parse_exchange_root(str(document))


def test_exchange_parser_rejects_symlink(tmp_path):
    document = tmp_path / "model.xml"
    document.write_text("<root/>", encoding="utf-8")
    link = tmp_path / "linked.xml"
    link.symlink_to(document)
    with pytest.raises(xml_security.ExchangeXmlError, match="regular"):
        xml_security.parse_exchange_root(str(link))


def test_exchange_parser_bounds_depth(tmp_path, monkeypatch):
    document = tmp_path / "model.xml"
    document.write_text("<a><b><c><d/></c></b></a>", encoding="utf-8")
    monkeypatch.setattr(xml_security, "MAX_EXCHANGE_DEPTH", 3)
    with pytest.raises(xml_security.ExchangeXmlError, match="structure"):
        xml_security.parse_exchange_root(str(document))
