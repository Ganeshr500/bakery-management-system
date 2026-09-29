# services.py - inventory, orders and reports

import json
from datetime import datetime
from core import (
    db, log, DEFAULT_REORDER, NotFound, Duplicate, NoStock, BadInput,
    clean_id, clean_name, clean_cat, clean_price, clean_qty, clean_customer,
)


# ---------- inventory ----------
def add_item(a, b, c, d, e, f=DEFAULT_REORDER):
    # id, name, category, price, stock, reorder level
    a = clean_id(a)
    b = clean_name(b)
    c = clean_cat(c)
    d = clean_price(d)
    e = clean_qty(e, zero=True)
    with db() as x:
        if x.execute("select 1 from items where item_id = ?", (a,)).fetchone():
            raise Duplicate(f"An item with ID '{a}' already exists.")
        x.execute("insert into items (item_id, name, category, unit_price, stock_qty, reorder_level) values (?, ?, ?, ?, ?, ?)", (a, b, c, d, e, f))
    log.info(f"added item {a} ({e} units @ {d})")
    return get_item(a)


def get_item(a):
    a = a.strip().upper()
    with db() as x:
        r = x.execute("select * from items where item_id = ?", (a,)).fetchone()
    if r is None:
        raise NotFound(f"No item found with ID '{a}'.")
    return dict(r)


def list_items():
    with db() as x:
        rows = x.execute("select * from items order by item_id").fetchall()
    return [dict(r) for r in rows]


def update_price(a, p):
    a = a.strip().upper()
    p = clean_price(p)
    with db() as x:
        n = x.execute("update items set unit_price = ? where item_id = ?", (p, a)).rowcount
    if n == 0:
        raise NotFound(f"No item found with ID '{a}'.")
    log.info(f"price of {a} set to {p}")
    return get_item(a)


def restock(a, q):
    a = a.strip().upper()
    q = clean_qty(q)
    with db() as x:
        n = x.execute("update items set stock_qty = stock_qty + ? where item_id = ?", (q, a)).rowcount
    if n == 0:
        raise NotFound(f"No item found with ID '{a}'.")
    log.info(f"restocked {a} by {q}")
    return get_item(a)


def delete_item(a):
    a = a.strip().upper()
    with db() as x:
        n = x.execute("delete from items where item_id = ?", (a,)).rowcount
    if n == 0:
        raise NotFound(f"No item found with ID '{a}'.")
    log.info(f"deleted item {a}")


# ---------- orders ----------
def make_order(r):
    o = dict(r)
    o["line_items"] = json.loads(o["line_items"])
    return o


def place_order(name, cart):
    # cart is {item_id: qty}. everything happens in one transaction,
    # so if any line fails nothing is deducted
    name = clean_customer(name)
    if not cart:
        raise BadInput("Cannot place an order with an empty cart.")
    with db() as x:
        lines = {}
        prices = {}
        for k, q in cart.items():
            k = k.strip().upper()
            q = clean_qty(q)
            r = x.execute("select unit_price, stock_qty from items where item_id = ?", (k,)).fetchone()
            if r is None:
                raise NotFound(f"No item found with ID '{k}'.")
            lines[k] = lines.get(k, 0) + q
            prices[k] = r["unit_price"]
            if lines[k] > r["stock_qty"]:
                raise NoStock(f"Not enough stock for '{k}': wanted {lines[k]}, only {r['stock_qty']} left.")

        total = 0.0
        for k, q in lines.items():
            x.execute("update items set stock_qty = stock_qty - ? where item_id = ?", (q, k))
            total += prices[k] * q
        total = round(total, 2)

        last = x.execute("select max(cast(substr(order_id, 4) as integer)) from orders").fetchone()[0] or 0
        oid = f"ORD{last + 1:04d}"
        when = datetime.now().isoformat(timespec="seconds")
        x.execute("insert into orders (order_id, customer_name, line_items, total_amount, timestamp, status) values (?, ?, ?, ?, ?, ?)", (oid, name, json.dumps(lines), total, when, "COMPLETED"))
    log.info(f"placed order {oid} for {name}, total {total}")
    return get_order(oid)


def get_order(a):
    a = a.strip().upper()
    with db() as x:
        r = x.execute("select * from orders where order_id = ?", (a,)).fetchone()
    if r is None:
        raise NotFound(f"No order found with ID '{a}'.")
    return make_order(r)


def list_orders():
    with db() as x:
        rows = x.execute("select * from orders order by order_id desc").fetchall()
    return [make_order(r) for r in rows]


def cancel_order(a):
    a = a.strip().upper()
    with db() as x:
        r = x.execute("select * from orders where order_id = ?", (a,)).fetchone()
        if r is None:
            raise NotFound(f"No order found with ID '{a}'.")
        if r["status"] == "CANCELLED":
            raise BadInput(f"Order '{a}' is already cancelled.")
        for k, q in json.loads(r["line_items"]).items():
            x.execute("update items set stock_qty = stock_qty + ? where item_id = ?", (q, k))
        x.execute("update orders set status = ? where order_id = ?", ("CANCELLED", a))
    log.info(f"cancelled order {a}, stock restored")
    return get_order(a)


# ---------- reports ----------
LINE = "=" * 46


def low_stock_report():
    with db() as x:
        rows = x.execute("select * from items where stock_qty <= reorder_level order by item_id").fetchall()
    out = [LINE, " LOW STOCK ALERT REPORT", LINE]
    if not rows:
        out.append("  All items are adequately stocked.")
    else:
        out.append(f"  {'Item ID':<10}{'Name':<20}{'Stock':<8}{'Reorder Lvl':<12}")
        out.append("-" * 46)
        for r in rows:
            out.append(f"  {r['item_id']:<10}{r['name']:<20}{r['stock_qty']:<8}{r['reorder_level']:<12}")
    out.append(LINE)
    return "\n".join(out)


def revenue_summary():
    with db() as x:
        n, total = x.execute("select count(*), sum(total_amount) from orders where status = 'COMPLETED'").fetchone()
    out = [LINE, " REVENUE SUMMARY", LINE]
    if n == 0:
        out.append("  No completed orders yet.")
    else:
        out.append(f"  Completed orders     : {n}")
        out.append(f"  Total revenue        : {total:.2f}")
        out.append(f"  Average order value  : {total / n:.2f}")
    out.append(LINE)
    return "\n".join(out)


def best_sellers_report(top=5):
    sold = {}
    for o in list_orders():
        if o["status"] == "COMPLETED":
            for k, q in o["line_items"].items():
                sold[k] = sold.get(k, 0) + q
    names = {i["item_id"]: i["name"] for i in list_items()}

    out = [LINE, f" TOP {top} BEST-SELLING ITEMS", LINE]
    if not sold:
        out.append("  No sales recorded yet.")
    else:
        out.append(f"  {'Rank':<6}{'Item ID':<10}{'Name':<20}{'Units Sold':<10}")
        out.append("-" * 46)
        best = sorted(sold.items(), key=lambda kv: kv[1], reverse=True)[:top]
        for n, (k, q) in enumerate(best, start=1):
            out.append(f"  {n:<6}{k:<10}{names.get(k, '(deleted item)'):<20}{q:<10}")
    out.append(LINE)
    return "\n".join(out)
