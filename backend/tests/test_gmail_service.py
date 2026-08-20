"""
GmailService gövde çıkarma (body extraction) regresyon testleri.

Pazarlama e-postalarında text/plain sık sık bir-iki kelimelik boş bir
"yedek" oluyor (gerçek içerik HTML'de) — eskiden ilk bulunan dolu parçayı
döndüren kod, bu yüzden "Tam metni gör" panelinde neredeyse hiçbir şey
göstermiyordu. Artık en uzun (= en zengin) adayı seçiyor.
"""
import base64
from backend.automation.gmail_service import GmailService


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


def test_extract_api_body_prefers_richer_html_over_sparse_plain_text():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": _b64("LinkedIn")}},
            {
                "mimeType": "text/html",
                "body": {"data": _b64("<html><body><h1>LinkedIn Premium</h1><p>Değerli bir üyemiz olduğunuz için teşekkür ederiz. Kariyeriniz hakkında güncellemeler burada.</p></body></html>")},
            },
        ],
    }

    result = GmailService._extract_api_body(payload)

    assert "LinkedIn Premium" in result
    assert "güncellemeler" in result


def test_extract_api_body_falls_back_to_plain_text_when_no_html():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": _b64("Sadece düz metin bir e-posta içeriği burada.")}},
        ],
    }

    result = GmailService._extract_api_body(payload)

    assert result == "Sadece düz metin bir e-posta içeriği burada."


def test_extract_api_body_handles_nested_multipart():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {
                "mimeType": "multipart/alternative",
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": _b64("kısa")}},
                    {"mimeType": "text/html", "body": {"data": _b64("<p>Bu iç içe geçmiş çok daha uzun ve gerçek e-posta içeriği burada yer alıyor.</p>")}},
                ],
            }
        ],
    }

    result = GmailService._extract_api_body(payload)

    assert "gerçek e-posta içeriği" in result


def test_extract_api_body_returns_empty_string_for_no_content():
    assert GmailService._extract_api_body({"mimeType": "multipart/mixed", "parts": []}) == ""
