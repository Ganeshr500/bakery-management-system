# BakeryHub 🥐

A small console app for running a bakery's stock and orders. You add items,
sell them, and the app keeps the numbers straight: stock goes down when an
order is placed and comes back if the order is cancelled. It can also tell
you what's running low and what's selling best.

Made for the VITyarthi "Build Your Own Project" submission (Python, first
semester). Everything is saved in a local SQLite database, and it needs
nothing beyond standard Python.

## What it can do

- **Manage items:** add, view, change the price, restock, delete
  (bread, cakes, pastries, cookies, beverages)
- **Take orders:** put several items in one order. Stock is checked first,
  and if any line fails nothing gets deducted
- **Cancel orders:** stock is put back automatically
- **Reports:** low-stock alerts, revenue summary, top 5 best sellers
- **Safe with input:** every value is validated, and all database queries use
  `?` placeholders so typed text can't mess with the SQL
- **Logging:** everything is written to `logs/app.log`

## Getting started

You need Python 3.8 or newer.

```bash
git clone https://github.com/Ganeshr500/bakery-hub.git
cd bakeryhub
python3 main.py
```

That's it. The `data/` and `logs/` folders are created the first time it runs.
If you have old `data/items.json` / `data/orders.json` files from the earlier
JSON version, they're imported into the database automatically (only if the
database is still empty).

## Using it

You get a numbered menu:

```
 1. Add new item          7. Place new order
 2. View all items        8. View order details
 3. View one item         9. Cancel an order
 4. Update item price    10. Low stock report
 5. Restock item         11. Revenue summary
 6. Delete item          12. Best-sellers report
 0. Exit
```

A quick first run: add a couple of items with option 1, sell some with option
7 (leave the item ID blank when you're done adding lines), then check
options 10 to 12.

## How the code is laid out

```
bakeryhub/
├── main.py            # the menu / what you see on screen
├── services.py        # inventory, orders and reports
├── core.py            # settings, errors, input checks, sqlite helper
├── tests/
│   └── test_bakeryhub.py
├── requirements.txt   # nothing to install
├── statement.txt      # problem statement
├── README.md
└── .gitignore
```

Two tables live in `data/bakeryhub.db`: `items` and `orders`. An order's
items are stored as a small JSON string like `{"BR001": 2, "CK001": 6}`.

## Running the tests

```bash
python -m unittest tests/test_bakeryhub.py -v
```

The tests use a temporary database, so your real bakery data is never touched.

## Built with

Python 3 and its standard library only: `sqlite3`, `json`, `logging`, `re`,
`unittest`, `datetime`. Git for version control.

## Good to know

- Item IDs are stored in capitals, so `br001` and `BR001` are the same item.
- Price limit is 5000 and the limit per order line is 500. Both can be changed
  at the top of `core.py`.
- Deleting an item doesn't delete old orders. The best-sellers report just
  shows "(deleted item)" for it.

## Author

Built as part of the VITyarthi "Build Your Own Project" submission
(Python, first semester).
