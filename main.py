# main.py - menu driven console app for BakeryHub

import services as s
from core import CATEGORIES, BakeryError, log

MENU = """
=========================================
        BAKERYHUB - MAIN MENU
=========================================
 1. Add new item
 2. View all items
 3. View one item's details
 4. Update item price
 5. Restock item
 6. Delete item
 7. Place new order
 8. View order details
 9. Cancel an order
10. Low stock report
11. Revenue summary
12. Best-sellers report
 0. Exit
=========================================
"""


def ask(t):
    return input(t).strip()


def add():
    a = ask("Item ID (e.g. BR001): ")
    b = ask("Item name: ")
    print(f"Categories: {', '.join(CATEGORIES)}")
    c = ask("Category: ")
    d = ask("Unit price: ")
    e = ask("Initial stock quantity: ")
    i = s.add_item(a, b, c, d, e)
    print(f"✔ Added: {i['item_id']} - {i['name']} ({i['stock_qty']} in stock)")


def show_all():
    rows = s.list_items()
    if not rows:
        print("No items in inventory yet.")
        return
    print(f"\n{'ID':<8}{'Name':<20}{'Category':<10}{'Price':<10}{'Stock':<8}")
    print("-" * 56)
    for i in rows:
        low = " (LOW)" if i["stock_qty"] <= i["reorder_level"] else ""
        print(f"{i['item_id']:<8}{i['name']:<20}{i['category']:<10}{i['unit_price']:<10}{str(i['stock_qty']) + low:<8}")


def show_one():
    i = s.get_item(ask("Item ID: "))
    print(f"\nID: {i['item_id']} | {i['name']} | {i['category']}")
    print(f"Price: {i['unit_price']} | Stock: {i['stock_qty']} | Reorder level: {i['reorder_level']}")


def price():
    a = ask("Item ID: ")
    b = ask("New price: ")
    i = s.update_price(a, b)
    print(f"✔ {i['item_id']} price is now {i['unit_price']}")


def restock():
    a = ask("Item ID: ")
    b = ask("Additional quantity: ")
    i = s.restock(a, b)
    print(f"✔ {i['item_id']} stock is now {i['stock_qty']}")


def delete():
    a = ask("Item ID: ")
    s.delete_item(a)
    print(f"✔ Deleted item {a.upper()}")


def order():
    name = ask("Customer name: ")
    cart = {}
    print("Enter items for this order. Leave Item ID blank to finish.")
    while True:
        a = ask("  Item ID: ")
        if not a:
            break
        cart[a] = ask("  Quantity: ")
    o = s.place_order(name, cart)
    print(f"✔ Order placed: {o['order_id']} | Total: {o['total_amount']}")


def show_order():
    o = s.get_order(ask("Order ID: "))
    print(f"\nOrder {o['order_id']} | {o['customer_name']} | {o['status']}")
    print(f"Items: {o['line_items']}")
    print(f"Total: {o['total_amount']} | Placed: {o['timestamp']}")


def cancel():
    o = s.cancel_order(ask("Order ID to cancel: "))
    print(f"✔ Order {o['order_id']} cancelled, stock restored.")


ACTIONS = {
    "1": add,
    "2": show_all,
    "3": show_one,
    "4": price,
    "5": restock,
    "6": delete,
    "7": order,
    "8": show_order,
    "9": cancel,
    "10": lambda: print(s.low_stock_report()),
    "11": lambda: print(s.revenue_summary()),
    "12": lambda: print(s.best_sellers_report()),
}


def main():
    log.info("app started")
    print("Welcome to BakeryHub!")
    while True:
        print(MENU)
        c = ask("Enter choice: ")
        if c == "0":
            print("Goodbye!")
            log.info("app exited")
            break
        f = ACTIONS.get(c)
        if f is None:
            print("Invalid choice, please try again.")
            continue
        try:
            f()
        except BakeryError as e:
            print(f"⚠ Error: {e}")
            log.warning(f"handled error: {e}")
        except Exception as e:
            print("⚠ Something went wrong. Check logs/app.log for details.")
            log.exception(f"unexpected error: {e}")


if __name__ == "__main__":
    main()
