# tests for bakeryhub - each test gets its own throwaway database

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core
import services as s
from core import NotFound, Duplicate, NoStock, BadInput


class BakeryTests(unittest.TestCase):

    def setUp(self):
        self.old = core.DB_FILE
        self.tmp = tempfile.mkdtemp()
        core.DB_FILE = os.path.join(self.tmp, "test.db")
        s.add_item("BR001", "Sourdough", "Bread", 120, 20)
        s.add_item("CK001", "Choc Cookie", "Cookie", 30, 50)

    def tearDown(self):
        core.DB_FILE = self.old
        if os.path.exists(os.path.join(self.tmp, "test.db")):
            os.remove(os.path.join(self.tmp, "test.db"))
        os.rmdir(self.tmp)

    def stock(self, a):
        return s.get_item(a)["stock_qty"]

    # inventory
    def test_add_and_get_item(self):
        i = s.get_item("br001")
        self.assertEqual(i["name"], "Sourdough")
        self.assertEqual(i["unit_price"], 120.0)

    def test_duplicate_item(self):
        with self.assertRaises(Duplicate):
            s.add_item("br001", "Another", "Bread", 10, 1)

    def test_bad_category(self):
        with self.assertRaises(BadInput):
            s.add_item("XX1", "Thing", "Pizza", 10, 1)

    def test_bad_prices(self):
        for p in ["abc", "-5", "0", "nan", "999999"]:
            with self.assertRaises(BadInput):
                s.update_price("BR001", p)

    def test_update_price(self):
        self.assertEqual(s.update_price("BR001", "150.5")["unit_price"], 150.5)

    def test_restock(self):
        s.restock("BR001", 10)
        self.assertEqual(self.stock("BR001"), 30)

    def test_delete_item(self):
        s.delete_item("BR001")
        with self.assertRaises(NotFound):
            s.get_item("BR001")

    def test_missing_item(self):
        with self.assertRaises(NotFound):
            s.restock("NOPE", 1)

    def test_sql_text_is_harmless(self):
        s.add_item("BN1", "Baker's Bun", "Bread", 10, 5)
        self.assertEqual(s.get_item("BN1")["name"], "Baker's Bun")
        with self.assertRaises(NotFound):
            s.get_item("x' or '1'='1")
        self.assertEqual(len(s.list_items()), 3)

    # orders
    def test_place_order(self):
        o = s.place_order("Asha", {"br001": 2, "CK001": 10})
        self.assertEqual(o["total_amount"], 540.0)
        self.assertEqual(self.stock("BR001"), 18)
        self.assertEqual(self.stock("CK001"), 40)

    def test_not_enough_stock(self):
        with self.assertRaises(NoStock):
            s.place_order("Asha", {"BR001": 21})
        self.assertEqual(self.stock("BR001"), 20)

    def test_failed_order_deducts_nothing(self):
        with self.assertRaises(NotFound):
            s.place_order("Asha", {"BR001": 5, "ZZ9": 1})
        self.assertEqual(self.stock("BR001"), 20)

    def test_empty_cart(self):
        with self.assertRaises(BadInput):
            s.place_order("Asha", {})

    def test_order_ids_count_up(self):
        a = s.place_order("Asha", {"BR001": 1})
        b = s.place_order("Ravi", {"BR001": 1})
        self.assertEqual((a["order_id"], b["order_id"]), ("ORD0001", "ORD0002"))

    def test_cancel_restores_stock(self):
        o = s.place_order("Asha", {"BR001": 5})
        s.cancel_order(o["order_id"])
        self.assertEqual(self.stock("BR001"), 20)
        self.assertEqual(s.get_order(o["order_id"])["status"], "CANCELLED")

    def test_cancel_twice(self):
        o = s.place_order("Asha", {"BR001": 5})
        s.cancel_order(o["order_id"])
        with self.assertRaises(BadInput):
            s.cancel_order(o["order_id"])

    # reports
    def test_low_stock_report(self):
        s.place_order("Asha", {"BR001": 15})
        r = s.low_stock_report()
        self.assertIn("BR001", r)
        self.assertNotIn("CK001", r)

    def test_revenue_ignores_cancelled(self):
        a = s.place_order("Asha", {"BR001": 1})
        s.place_order("Ravi", {"CK001": 1})
        s.cancel_order(a["order_id"])
        r = s.revenue_summary()
        self.assertIn("Completed orders     : 1", r)
        self.assertIn("30.00", r)

    def test_best_sellers_order(self):
        s.place_order("Asha", {"BR001": 2, "CK001": 9})
        r = s.best_sellers_report()
        self.assertLess(r.index("CK001"), r.index("BR001"))


if __name__ == "__main__":
    unittest.main()
