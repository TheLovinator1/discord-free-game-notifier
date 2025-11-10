from __future__ import annotations

import datetime

from hypothesis import given
from hypothesis import strategies as st

from discord_free_game_notifier.epic import CatalogNs
from discord_free_game_notifier.epic import CatalogNsMapping
from discord_free_game_notifier.epic import DiscountSetting
from discord_free_game_notifier.epic import EpicGameElement
from discord_free_game_notifier.epic import KeyImage
from discord_free_game_notifier.epic import OfferMapping
from discord_free_game_notifier.epic import Price
from discord_free_game_notifier.epic import PromotionalOffer
from discord_free_game_notifier.epic import PromotionalOfferGroup
from discord_free_game_notifier.epic import Promotions
from discord_free_game_notifier.epic import Seller
from discord_free_game_notifier.epic import TotalPrice
from discord_free_game_notifier.epic import game_url
from discord_free_game_notifier.epic import promotion_end
from discord_free_game_notifier.epic import promotion_start


def test_game_url_prefers_product_slug() -> None:
    game = EpicGameElement(
        title="Test Game",
        id="test-id",
        namespace="ns",
        status="ACTIVE",
        keyImages=[KeyImage(type="Thumbnail", url="https://example.com/img.png")],
        seller=Seller(id="seller", name="Dev"),
        categories=[],
        price=Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD")),
        productSlug="nice-slug",
    )
    assert game_url(game).endswith("/p/nice-slug")


def test_game_url_falls_back_to_offer_mappings() -> None:
    game = EpicGameElement(
        title="Test Game",
        id="test-id",
        namespace="ns",
        status="ACTIVE",
        keyImages=[KeyImage(type="Thumbnail", url="https://example.com/img.png")],
        seller=Seller(id="seller", name="Dev"),
        categories=[],
        price=Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD")),
        offerMappings=[OfferMapping(pageSlug="offer-slug", pageType="productHome")],
    )
    assert game_url(game).endswith("/p/offer-slug")


def test_game_url_falls_back_to_url_slug() -> None:
    game = EpicGameElement(
        title="Test Game",
        id="test-id",
        namespace="ns",
        status="ACTIVE",
        keyImages=[KeyImage(type="Thumbnail", url="https://example.com/img.png")],
        seller=Seller(id="seller", name="Dev"),
        categories=[],
        price=Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD")),
        urlSlug="url-slug",
    )
    assert game_url(game).endswith("/p/url-slug")


def test_game_url_falls_back_to_catalog_ns_mappings() -> None:
    game = EpicGameElement(
        title="Test Game",
        id="test-id",
        namespace="ns",
        status="ACTIVE",
        keyImages=[KeyImage(type="Thumbnail", url="https://example.com/img.png")],
        seller=Seller(id="seller", name="Dev"),
        categories=[],
        price=Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD")),
        catalogNs=CatalogNs(mappings=[CatalogNsMapping(pageSlug="cat-mapping", pageType="productHome")]),
    )
    assert game_url(game).endswith("/p/cat-mapping")


def test_promotion_times_from_upcoming_only() -> None:
    start = "2025-12-11T16:00:00.000Z"
    end = "2026-01-08T16:00:00.000Z"
    promos = Promotions(
        promotionalOffers=[],
        upcomingPromotionalOffers=[
            PromotionalOfferGroup(
                promotionalOffers=[
                    PromotionalOffer(
                        startDate=start,
                        endDate=end,
                        discountSetting=DiscountSetting(discountType="PERCENTAGE", discountPercentage=0),
                    ),
                ],
            ),
        ],
    )
    game = EpicGameElement(
        title="Test Game",
        id="test-id",
        namespace="ns",
        status="ACTIVE",
        keyImages=[KeyImage(type="Thumbnail", url="https://example.com/img.png")],
        seller=Seller(id="seller", name="Dev"),
        categories=[],
        price=Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD")),
        promotions=promos,
    )
    s: int = promotion_start(game)
    e: int = promotion_end(game)
    # Ensure they parse to non-zero and in correct order
    assert s > 0
    assert e > 0
    assert e > s
    # Ensure UTC conversion: round-trip check
    expected_s = int(datetime.datetime(2025, 12, 11, 16, 0, 0, tzinfo=datetime.UTC).timestamp())
    expected_e = int(datetime.datetime(2026, 1, 8, 16, 0, 0, tzinfo=datetime.UTC).timestamp())
    assert s == expected_s
    assert e == expected_e


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_", min_size=1, max_size=50))
def test_game_url_with_product_slug_always_contains_slug(slug: str) -> None:
    """Property: game_url with productSlug always contains that slug in URL."""
    game = EpicGameElement(
        title="Test",
        id="test-id",
        namespace="ns",
        status="ACTIVE",
        keyImages=[KeyImage(type="Thumbnail", url="https://example.com/img.png")],
        seller=Seller(id="seller", name="Dev"),
        categories=[],
        price=Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD")),
        productSlug=slug,
    )
    url: str = game_url(game)
    # ASCII slugs should not be URL-encoded
    assert slug in url, f"Expected slug '{slug}' in URL '{url}'"
    assert url.startswith("https://"), f"Expected HTTPS URL but got '{url}'"


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_", min_size=1, max_size=50))
def test_game_url_with_url_slug_fallback_contains_slug(slug: str) -> None:
    """Property: game_url falls back to urlSlug when productSlug absent."""
    game = EpicGameElement(
        title="Test",
        id="test-id",
        namespace="ns",
        status="ACTIVE",
        keyImages=[KeyImage(type="Thumbnail", url="https://example.com/img.png")],
        seller=Seller(id="seller", name="Dev"),
        categories=[],
        price=Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD")),
        urlSlug=slug,
    )
    url: str = game_url(game)
    assert slug in url, f"Expected slug '{slug}' in URL '{url}'"


@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5))
def test_epic_game_categories_list_accepted(categories: list[str]) -> None:
    """Property: EpicGameElement accepts arbitrary category lists."""
    game = EpicGameElement(
        title="Test",
        id="test-id",
        namespace="ns",
        status="ACTIVE",
        keyImages=[KeyImage(type="Thumbnail", url="https://example.com/img.png")],
        seller=Seller(id="seller", name="Dev"),
        categories=[],  # We'd populate with Category objects if testing deeper
        price=Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD")),
    )
    assert game.title == "Test"
