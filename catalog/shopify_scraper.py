import requests
import re
from bs4 import BeautifulSoup

def fetch_products_page(shop_url: str, page: int = 1, limit: int = 250):
    """
    Fetch a page of products from a Shopify store.

    Args:
        shop_url (str): The base URL of the Shopify store.
        page (int, optional): The page number to fetch. Defaults to 1.
        limit (int, optional): The number of products per page. Defaults to 250.

    Returns:
        dict: The JSON response containing the products.
    """
    url = f"{shop_url}/products.json?page={page}&limit={limit}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data["products"]

def fetch_all_products(shop_url: str):
    """
    Fetch all products from a Shopify store by iterating through all pages.

    Args:
        shop_url (str): The base URL of the Shopify store.

    Returns:
        list: A list of all products from the store.
    """
    all_products = []
    page = 1
    while True:
        products = fetch_products_page(shop_url, page=page)
        if not products:
            break
        all_products.extend(products)
        page += 1
    return all_products

def strip_html(html: str) -> str:
    """Convertit du HTML en texte brut, sans balises."""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

def extract_book_data(product: dict, shop_url: str, money_format: str) -> dict:
    """
    Extract relevant book data from a Shopify product.

    Args:
        product (dict): The Shopify product data.
        shop_url (str): The base URL of the Shopify store.

    Returns:
        dict: A dictionary containing the extracted book data.
    """

    return {
        "title": product.get("title"),
        "url": f"{shop_url}/products/{product.get('handle')}",
        "price": format_price(product.get("variants", [{}])[0].get("price"), money_format),
        "synopsis": strip_html(product.get("body_html"))
    }

def fetch_shop_meta(shop_url: str) -> dict:
    """
    Fetch the meta information of a Shopify store.

    Args:
        shop_url (str): The base URL of the Shopify store.

    Returns:
        dict: The JSON response containing the shop meta information.
    """
    url = f"{shop_url}/meta.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def format_price(amount: str, money_format: str) -> str:
    """
    Format a price amount according to the given money format.

    Args:
        amount (str): The price amount as a string.
        money_format (str): The money format string, e.g., "${{amount}}".

    Returns:
        str: The formatted price string.
    """
    if "comma_separator" in money_format:
        amount = amount.replace(".", ",")
    return re.sub(r"\{\{.*?\}\}", amount, money_format)
