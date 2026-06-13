"""
Master Product Management for eResto Analysis.

Manages the fixed/master product list that is used in the daily sales
summary matrix. The product list order is preserved and consistent.
"""
import json
import os

from config import MASTER_PRODUCTS_FILE


def load_master_products() -> list[str]:
    """Load master product list from JSON file.

    Returns:
        List of product names in the configured order.
    """
    if not os.path.exists(MASTER_PRODUCTS_FILE):
        return []
    with open(MASTER_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('products', [])


def save_master_products(products: list[str]) -> None:
    """Save master product list to JSON file.

    Args:
        products: Ordered list of product names.
    """
    with open(MASTER_PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'products': products}, f, ensure_ascii=False, indent=2)


def add_product(name: str) -> list[str]:
    """Add a new product to the master list.

    Args:
        name: Product name to add.

    Returns:
        Updated product list.
    """
    products = load_master_products()
    name = name.strip()
    if name and name not in products:
        products.append(name)
        save_master_products(products)
    return products


def remove_product(name: str) -> list[str]:
    """Remove a product from the master list.

    Args:
        name: Product name to remove.

    Returns:
        Updated product list.
    """
    products = load_master_products()
    products = [p for p in products if p != name.strip()]
    save_master_products(products)
    return products


def reorder_products(products: list[str]) -> list[str]:
    """Replace the entire product list with a new ordered list.

    Args:
        products: New ordered list of product names.

    Returns:
        The saved product list.
    """
    cleaned = [p.strip() for p in products if p.strip()]
    save_master_products(cleaned)
    return cleaned
