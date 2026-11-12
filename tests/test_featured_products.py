import json
import unittest
from decimal import Decimal

from bs4 import BeautifulSoup

from backend.services.mthandizi_parser import (
    FeaturedProduct,
    parse_business_profile,
    parse_directory_businesses,
    parse_featured_products,
)


class FeaturedProductParsingTests(unittest.TestCase):
    def test_parses_directory_and_profile_details(self) -> None:
        directory_html = """
            <a href="/partners/example-business">
              <h3>Example Business</h3>
              <div><svg class="lucide-map-pin"></svg><span>Area 10</span></div>
            </a>
        """
        businesses = parse_directory_businesses(
            directory_html, "https://mthandizi.com/businesses-in-lilongwe"
        )
        profile = parse_business_profile(
            '<a href="https://wa.me/265991234567">WhatsApp</a>'
            '<a href="mailto:hello@example.com">Email</a>',
            businesses[0].profile_url,
        )

        self.assertEqual(businesses[0].business_name, "Example Business")
        self.assertEqual(
            businesses[0].profile_url,
            "https://mthandizi.com/partners/example-business",
        )
        self.assertEqual(businesses[0].location, "Area 10")
        self.assertEqual(profile.phone_number, "265991234567")
        self.assertEqual(profile.email, "hello@example.com")
        self.assertEqual(profile.featured_products, [])

    def test_parses_products_from_html_cards(self) -> None:
        profile_url = "https://mthandizi.com/partners/example-business"
        html = """
            <section>
              <h2>Featured products</h2>
              <a href="/shop/example-business/example-product">
                <h3>Example Product</h3>
                <span class="bg-muted">Agriculture</span>
                <span>MWK 12,345.50</span>
              </a>
            </section>
        """

        products = parse_featured_products(
            BeautifulSoup(html, "html.parser"), profile_url
        )

        self.assertEqual(
            products,
            [
                FeaturedProduct(
                    listing_url=(
                        "https://mthandizi.com/shop/example-business/"
                        "example-product"
                    ),
                    listing_title="Example Product",
                    item_price=Decimal("12345.50"),
                    category="Agriculture",
                )
            ],
        )

    def test_parses_products_from_next_flight_data(self) -> None:
        profile_url = "https://mthandizi.com/partners/example-business"
        card = [
            "$",
            "$L41",
            "product-id",
            {
                "href": "/shop/example-business/example-product?ref=partner_profile",
                "children": ["$L48"],
            },
        ]
        details = [
            "$",
            "div",
            None,
            {
                "children": [
                    ["$", "h3", None, {"children": "Example Product"}],
                    [
                        "$",
                        "span",
                        None,
                        {
                            "className": "rounded-full bg-muted",
                            "children": "Agriculture",
                        },
                    ],
                    [
                        "$",
                        "span",
                        None,
                        {"className": "font-bold", "children": "MWK 12,345.50"},
                    ],
                ]
            },
        ]
        flight_data = "\n".join(
            (f"47:{json.dumps(card)}", f"48:{json.dumps(details)}")
        )
        html = (
            "<script>self.__next_f.push([1,"
            f"{json.dumps(flight_data)}"
            "]);</script>"
        )

        products = parse_featured_products(
            BeautifulSoup(html, "html.parser"), profile_url
        )

        self.assertEqual(
            products,
            [
                FeaturedProduct(
                    listing_url=(
                        "https://mthandizi.com/shop/example-business/"
                        "example-product?ref=partner_profile"
                    ),
                    listing_title="Example Product",
                    item_price=Decimal("12345.50"),
                    category="Agriculture",
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
