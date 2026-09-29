# core.py - settings, errors, input checks and the sqlite helper

import os
import re
import json
import sqlite3
import logging
from contextlib import contextmanager

# paths
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
LOG_DIR = os.path.join(BASE, "logs")
DB_FILE = os.path.join(DATA_DIR, "bakeryhub.db")
OLD_ITEMS = os.path.join(DATA_DIR, "items.json")
OLD_ORDERS = os.path.join(DATA_DIR, "orders.json")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

CATEGORIES = ["Bread", "Cake", "Pastry", "Cookie", "Beverage"]
DEFAULT_REORDER = 10
MAX_PRICE = 5000.0
MAX_QTY = 500

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "app.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("bakeryhub")


# errors
class BakeryError(Exception):
    pass


class NotFound(BakeryError):
    pass


class Duplicate(BakeryError):
    pass


class NoStock(BakeryError):
    pass


class BadInput(BakeryError):
    pass


class DBError(BakeryError):
    pass


# input checks
def clean_id(a):
    a = a.strip().upper()
    if not re.match(r"^[A-Z0-9]{2,15}$", a):
        raise BadInput("Item ID must be 2-15 letters/numbers (e.g. BR001).")
    return a


def clean_name(a):
    a = a.strip()
    if not re.match(r"^[A-Za-z0-9 ,.'&-]{2,60}$", a):
        raise BadInput("Item name must be 2-60 characters (letters, numbers, spaces, & , . -).")
    return a


def clean_cat(a):
    a = a.strip().title()
    if a not in CATEGORIES:
        raise BadInput(f"Category must be one of: {', '.join(CATEGORIES)}.")
    return a


def clean_price(a):
    try:
        p = float(a)
    except (TypeError, ValueError):
        raise BadInput(f"Price must be a number, got '{a}'.")
    if not 0 < p <= MAX_PRICE:
        raise BadInput(f"Price must be between 0 and {MAX_PRICE}, got {p}.")
    return round(p, 2)


def clean_qty(a, zero=False):
    try:
        q = int(a)
    except (TypeError, ValueError):
        raise BadInput(f"Quantity must be a whole number, got '{a}'.")
    low = 0 if zero else 1
    if not low <= q <= MAX_QTY:
        raise BadInput(f"Quantity must be between {low} and {MAX_QTY}, got {q}.")
    return q


def clean_customer(a):
    a = a.strip()
    if not 2 <= len(a) <= 60:
        raise BadInput("Customer name must be 2-60 characters.")
    return a


# database
def connect():
    x = sqlite3.connect(DB_FILE)
    x.row_factory = sqlite3.Row
    x.execute("create table if not exists items (item_id text primary key, name text not null, category text not null, unit_price real not null, stock_qty integer not null, reorder_level integer not null)")
    x.execute("create table if not exists orders (order_id text primary key, customer_name text not null, line_items text not null, total_amount real not null, timestamp text not null, status text not null)")
    return x


@contextmanager
def db():
    # commits if the block finishes, rolls back if anything is raised
    x = connect()
    try:
        yield x
        x.commit()
    except sqlite3.Error as e:
        x.rollback()
        log.error(f"database error: {e}")
        raise DBError(f"Database problem: {e}")
    finally:
        x.close()


def read_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            t = f.read().strip()
            return json.loads(t) if t else {}
    except (json.JSONDecodeError, OSError) as e:
        log.warning(f"could not read {path}: {e}")
        return {}


def migrate():
    # one time import of old json files, only when the tables are empty
    with db() as x:
        if x.execute("select count(*) from items").fetchone()[0] == 0:
            for k, v in read_json(OLD_ITEMS).items():
                x.execute("insert or replace into items (item_id, name, category, unit_price, stock_qty, reorder_level) values (?, ?, ?, ?, ?, ?)", (k, v["name"], v["category"], v["unit_price"], v["stock_qty"], v.get("reorder_level", 10)))
        if x.execute("select count(*) from orders").fetchone()[0] == 0:
            for k, v in read_json(OLD_ORDERS).items():
                x.execute("insert or replace into orders (order_id, customer_name, line_items, total_amount, timestamp, status) values (?, ?, ?, ?, ?, ?)", (k, v["customer_name"], json.dumps(v["line_items"]), v["total_amount"], v["timestamp"], v.get("status", "COMPLETED")))


migrate()
