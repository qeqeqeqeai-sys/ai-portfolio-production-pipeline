from __future__ import annotations

SAMPLE_REGISTRY_SOURCES = {
    "fixture_us_listings": [
        {
            "source_url": "file://fixtures/tier3h5_fixture_us_listings.json",
            "issuer_name": "Example Holdings Inc.",
            "country_code": "US",
            "primary_exchange": "NASDAQ",
            "ticker": "EXM",
            "issuer_type": "operating_company",
            "sec_cik": "0001234567",
            "lei": "5493001KJTIIGC8Y1R12",
            "security_name": "Example Holdings Common Stock",
            "security_type": "common_stock",
            "currency": "USD",
        }
    ],
    "fixture_cross_listing": [
        {
            "source_url": "file://fixtures/tier3h5_fixture_cross_listing.json",
            "issuer_name": "Example Holdings Inc",
            "country_code": "US",
            "primary_exchange": "NYSE",
            "ticker": "EXM",
            "issuer_type": "operating_company",
            "sec_cik": "0001234567",
            "lei": "5493001KJTIIGC8Y1R12",
            "security_name": "Example Holdings Preferred",
            "security_type": "preferred_stock",
            "currency": "USD",
        }
    ],
}
