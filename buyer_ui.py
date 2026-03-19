# buyer_ui.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, simpledialog
import db, json
from utils import gen_txid

# PDF receipt support (optional)
try:
    from fpdf import FPDF
    HAVE_FPDF = True
except Exception:
    HAVE_FPDF = False


class BuyerApp(tb.Toplevel):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.cart = []
        self.title(f"Buyer — {user['username']}")
        self.geometry("980x600")
        self.configure(padx=10, pady=10, bg="#e6f9f0")
        self.build_ui()
        self.refresh_products()

    def build_ui(self):
        # Top frame for welcome and search
        top = tb.Frame(self, padding=8)
        top.pack(fill="x", pady=(0,8))
        tb.Label(top, text=f"Welcome, {self.user['username']}", font=("Arial", 12, "bold"), bootstyle="success").pack(side="left")
        tb.Label(top, text="Search:").pack(side="left", padx=(10,4))
        self.search_var = tk.StringVar()
        tb.Entry(top, textvariable=self.search_var, width=30, bootstyle="info").pack(side="left")
        tb.Button(top, text="Go", bootstyle="success", command=self.refresh_products).pack(side="left", padx=6)
        tb.Button(top, text="View Cart", bootstyle="warning", command=self.view_cart).pack(side="right")

        # Treeview for products
        cols = ("id","name","description","brand","price","stock","expiry")
        self.tree = tb.Treeview(self, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, anchor="w", width=120)
        self.tree.pack(fill="both", expand=True)

        # Bottom frame for actions
        bottom = tb.Frame(self, padding=8)
        bottom.pack(fill="x", pady=(8,0))
        tb.Button(bottom, text="Add to Cart", bootstyle="success", command=self.add_to_cart).pack(side="left")
        self.status = tb.Label(bottom, text="Browse products", bootstyle="info")
        self.status.pack(side="right")

    def refresh_products(self):
        q = self.search_var.get().strip().lower()
        for r in self.tree.get_children():
            self.tree.delete(r)
        products = db.list_products()
        for p in products:
            if q:
                if q not in p.get("name","").lower() and q not in p.get("brand","").lower() and q not in p.get("id","").lower():
                    continue
            self.tree.insert("", "end", iid=p["id"], values=(
                p["id"], p.get("name",""), p.get("description",""), 
                p.get("brand",""), f"{float(p.get('price',0)):.2f}", 
                p.get("stock",0), p.get("expiry","")
            ))
        self.status.config(text=f"{len(self.tree.get_children())} products — Cart: {len(self.cart)} items")

    def get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a product.")
            return None
        return db.get_product(sel[0])

    def add_to_cart(self):
        p = self.get_selected()
        if not p: return
        if p.get("stock",0) <= 0:
            messagebox.showerror("Out of stock", "This product has no stock.")
            return
        qty = simpledialog.askinteger("Quantity", f"Enter quantity (available: {p['stock']}):", minvalue=1, maxvalue=p['stock'], parent=self)
        if not qty: return
        for it in self.cart:
            if it["product_id"] == p["id"]:
                it["qty"] += qty
                break
        else:
            self.cart.append({"product_id": p["id"], "name": p["name"], "qty": qty, "unit_price": p["price"]})
        self.status.config(text=f"{len(self.tree.get_children())} products — Cart: {len(self.cart)} items")
        messagebox.showinfo("Cart", f"Added {qty} x {p['name']} to cart.")

    def view_cart(self):
        CartWindow(self, self.cart, self.checkout)

    def checkout(self, customer_name):
        # validate and deduct stock
        for it in self.cart:
            p = db.get_product(it["product_id"])
            if not p or p.get("stock",0) < it["qty"]:
                messagebox.showerror("Checkout", f"Not enough stock for {it['name']}")
                return
        items_for_tx = []
        total = 0.0
        for it in self.cart:
            p = db.get_product(it["product_id"])
            new_stock = p.get("stock",0) - it["qty"]
            db.update_product(p["id"], {"stock": new_stock})
            items_for_tx.append({"product_id": p["id"], "name": p["name"], "qty": it["qty"], "unit_price": p["price"]})
            total += it["qty"] * p["price"]
        txid = db.record_transaction(items_for_tx, total, customer=customer_name or self.user["username"])
        try:
            receipt_path = generate_receipt(txid, items_for_tx, total, customer_name or self.user["username"])
        except Exception:
            receipt_path = None
        self.cart.clear()
        self.refresh_products()
        msg = f"Order placed. Total: {total:.2f}\nTransaction ID: {txid}"
        if receipt_path:
            msg += f"\nReceipt: {receipt_path}"
        messagebox.showinfo("Order placed", msg)


def generate_receipt(txid, items, total, customer):
    if HAVE_FPDF:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"Receipt — Transaction {txid}", ln=1)
        pdf.cell(0, 6, f"Customer: {customer}", ln=1)
        pdf.cell(0, 6, "-"*60, ln=1)
        pdf.cell(60,6,"Item", border=0)
        pdf.cell(30,6,"Qty", border=0)
        pdf.cell(30,6,"Unit", border=0)
        pdf.cell(30,6,"Subtotal", ln=1)
        for it in items:
            pdf.cell(60,6,str(it["name"]))
            pdf.cell(30,6,str(it["qty"]))
            pdf.cell(30,6,f"{it['unit_price']:.2f}")
            pdf.cell(30,6,f"{it['qty']*it['unit_price']:.2f}", ln=1)
        pdf.cell(0,6,"-"*60, ln=1)
        pdf.cell(0,8, f"Total: {total:.2f}", ln=1)
        path = f"receipt_{txid}.pdf"
        pdf.output(path)
        return path
    else:
        path = f"receipt_{txid}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Receipt — Transaction {txid}\n")
            f.write(f"Customer: {customer}\n")
            f.write("-"*60 + "\n")
            f.write(f"{'Item':30}{'Qty':>5}{'Unit':>10}{'Subtotal':>12}\n")
            for it in items:
                f.write(f"{it['name'][:30]:30}{it['qty']:5}{it['unit_price']:10.2f}{it['qty']*it['unit_price']:12.2f}\n")
            f.write("-"*60 + "\n")
            f.write(f"Total: {total:.2f}\n")
        return path


class CartWindow(tb.Toplevel):
    def __init__(self, master, cart, on_checkout):
        super().__init__(master)
        self.cart = cart
        self.on_checkout = on_checkout
        self.title("Cart")
        self.geometry("600x420")
        self.configure(padx=10, pady=10, bg="#e6f9f0")
        self.build()

    def build(self):
        cols = ("name","qty","unit_price","subtotal")
        self.tree = tb.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        btnf = tb.Frame(self, padding=6)
        btnf.pack(fill="x")
        tb.Button(btnf, text="Remove Selected", bootstyle="danger", command=self.remove_selected).pack(side="left")
        tb.Button(btnf, text="Checkout", bootstyle="success", command=self.checkout).pack(side="right")
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for it in self.cart:
            self.tree.insert("", "end", iid=it["product_id"], values=(
                it["name"], it["qty"], f"{it['unit_price']:.2f}", f"{it['qty']*it['unit_price']:.2f}"
            ))
        total = sum(it['qty']*it['unit_price'] for it in self.cart)
        self.title(f"Cart — Total: {total:.2f}")

    def remove_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Remove", "Select an item to remove.")
            return
        pid = sel[0]
        self.cart[:] = [it for it in self.cart if it["product_id"] != pid]
        self.refresh()

    def checkout(self):
        if not self.cart:
            messagebox.showinfo("Checkout", "Cart is empty.")
            return
        cust = simpledialog.askstring("Customer name", "Customer name (optional):", parent=self)
        if cust is None:
            return
        self.on_checkout(cust)
        self.destroy()
