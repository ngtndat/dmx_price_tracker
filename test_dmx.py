import json
import requests
import re
import time
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.dienmayxanh.com"
}


def clean_price(text):

    if not text:
        return "0"

    nums = re.sub(r"[^\d]", "", str(text))

    return nums if nums else "0"


def parse_dmx_jsonld(soup):

    products = []

    scripts = soup.find_all(
        "script",
        type="application/ld+json"
    )

    print("JSON-LD:", len(scripts))

    for sc in scripts:

        try:

            raw = sc.get_text(strip=True)

            if not raw:
                continue

            data = json.loads(raw)

            if not isinstance(data, dict):
                continue

            main = data.get(
                "mainEntity"
            )

            if not isinstance(main, dict):
                continue

            items = main.get(
                "itemListElement"
            )

            if not items:
                continue

            print(
                "Products in JSON:",
                len(items)
            )

            for row in items:

                product = row.get(
                    "item"
                )

                if not product:
                    product = row

                name = product.get(
                    "name",
                    ""
                )

                url = product.get(
                    "url",
                    ""
                )

                if (
                    "LG"
                    not in name.upper()
                ):
                    continue

                products.append(
                    {
                        "name": name,
                        "url": url
                    }
                )

        except Exception as e:

            print(
                "JSON ERROR:",
                e
            )

    return products


def parse_dmx_detail(url):

    try:

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print(
            "DETAIL STATUS:",
            r.status_code
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        text = soup.get_text(
            " ",
            strip=True
        )

        m = re.search(
            r"([\d\.]+)\s*₫",
            text
        )

        price = (
            m.group(1)
            if m
            else ""
        )

        return {
            "price": price
        }

    except Exception as e:

        print(
            "DETAIL ERROR:",
            e
        )

        return {
            "price": ""
        }


def main():

    url = (
        "https://www.dienmayxanh.com/"
        "may-lanh-lg"
    )

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    print(
        "STATUS:",
        r.status_code
    )

    print(
        "HTML:",
        len(r.text)
    )

    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )

    products = parse_dmx_jsonld(
        soup
    )

    print(
        "\nTOTAL LG:",
        len(products)
    )

    for i, p in enumerate(
        products,
        1
    ):

        print(
            f"\n[{i}]",
            p["name"]
        )

        print(
            p["url"]
        )

        detail = parse_dmx_detail(
            p["url"]
        )

        print(
            detail
        )

        time.sleep(1)


if __name__ == "__main__":
    main()
