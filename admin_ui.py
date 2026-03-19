# admin_ui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import db
from utils import gen_pid
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import datetime

# Initialize ttkbootstrap style (greenish medical theme)
STYLE = tb.Style("minty")  # green medical theme

# ------------------ Admin App ------------------
class AdminApp(tb.Toplevel):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.title(f"Pharmacy Admin — {user['username']}")
        self.geometry("1000x600")
        self.configure(padx=10, pady=10, bg="#e6f9f0")
        self.build_ui()
        self.refresh()

    def build_ui(self):
        # Top Frame for action buttons
        top = tb.Frame(self, padding=10)
        top.pack(fill="x", pady=(0,10))

        btn_frame = tb.Frame(top)
        btn_frame.pack(side="left", anchor="w", padx=10)

        btn_style = {"bootstyle":"success-outline", "width":12}

        tb.Button(btn_frame, text="Add Product", command=self.add_product, **btn_style).pack(side="left", padx=4)
        tb.Button(btn_frame, text="Edit Product", command=self.edit_product, **btn_style).pack(side="left", padx=4)
        tb.Button(btn_frame, text="Delete Product", command=self.delete_product, **btn_style).pack(side="left", padx=4)
        tb.Button(btn_frame, text="Restock", command=self.restock_product, **btn_style).pack(side="left", padx=4)
        tb.Button(btn_frame, text="Sell", command=self.sell_product, **btn_style).pack(side="left", padx=4)
        tb.Button(btn_frame, text="Manage Users", command=self.manage_users, **btn_style).pack(side="left", padx=4)

        # ----------- Filter Frame -------------
        filter_frame = tb.Labelframe(self, text="Filters", padding=10, bootstyle="info")
        filter_frame.pack(fill="x", padx=10, pady=(0,10))

        tb.Label(filter_frame, text="Stock less than:").pack(side="left", padx=5)
        self.stock_filter = tb.Entry(filter_frame, width=8)
        self.stock_filter.pack(side="left")

        tb.Label(filter_frame, text="Expiry before (YYYY-MM-DD):").pack(side="left", padx=5)
        self.expiry_filter = tb.Entry(filter_frame, width=12)
        self.expiry_filter.pack(side="left")

        tb.Button(filter_frame, text="Apply", bootstyle="primary", command=self.apply_filters).pack(side="left", padx=8)
        tb.Button(filter_frame, text="Clear", bootstyle="secondary", command=self.clear_filters).pack(side="left", padx=4)

        # ----------- Treeview frame -----------
        tree_frame = tb.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id","name","brand","price","stock","expiry","description")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Treeview style
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), foreground="#006600")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.map("Treeview", background=[("selected", "#b3ffcc")], foreground=[("selected", "black")])

        for c in cols:
            self.tree.heading(c, text=c.title())
            if c == "description":
                self.tree.column(c, width=240, anchor="w")
            elif c == "price":
                self.tree.column(c, width=80, anchor="e")
            elif c == "stock":
                self.tree.column(c, width=70, anchor="center")
            else:
                self.tree.column(c, width=120, anchor="w")

    # -------------------- Refresh --------------------
    def refresh(self, stock_limit=None, expiry_limit=None):
        for r in self.tree.get_children():
            self.tree.delete(r)
        products = db.list_products()
        for p in products:
            pid = str(p.get("id",""))
            name = str(p.get("name","")).strip()
            brand = str(p.get("brand","")).strip()
            desc = str(p.get("description","")).strip()
            try:
                price = float(p.get("price",0))
            except:
                price = 0
            try:
                stock = int(p.get("stock",0))
            except:
                stock = 0
            expiry = str(p.get("expiry",""))

            # ----- Apply filters -----
            if stock_limit is not None and stock >= stock_limit:
                continue
            if expiry_limit:
                try:
                    exp_date = datetime.datetime.strptime(expiry, "%Y-%m-%d").date()
                    if exp_date >= expiry_limit:
                        continue
                except:
                    pass

            self.tree.insert("", "end", iid=pid, values=(pid, name, brand, f"{price:.2f}", stock, expiry, desc))

    def apply_filters(self):
        stock_limit = self.stock_filter.get().strip()
        expiry_limit = self.expiry_filter.get().strip()

        stock_limit = int(stock_limit) if stock_limit.isdigit() else None
        try:
            expiry_limit = datetime.datetime.strptime(expiry_limit, "%Y-%m-%d").date() if expiry_limit else None
        except ValueError:
            expiry_limit = None

        self.refresh(stock_limit=stock_limit, expiry_limit=expiry_limit)

    def clear_filters(self):
        self.stock_filter.delete(0, "end")
        self.expiry_filter.delete(0, "end")
        self.refresh()

    # -------------------- Product Operations --------------------
    def get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a product.")
            return None
        return db.get_product(sel[0])

    def add_product(self):
        dlg = ProductDialog(self, title="Add Product")
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            prod = dlg.result
            prod["id"] = gen_pid()
            db.add_product(prod)
            self.refresh()
            messagebox.showinfo("Added", f"Product '{prod['name']}' added.")

    def edit_product(self):
        p = self.get_selected()
        if not p: return
        dlg = ProductDialog(self, product=p, title="Edit Product")
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            db.update_product(p["id"], dlg.result)
            self.refresh()
            messagebox.showinfo("Updated", "Product updated.")

    def delete_product(self):
        p = self.get_selected()
        if not p: return
        if messagebox.askyesno("Confirm", f"Delete {p['name']} ({p['id']})?"):
            db.delete_product(p["id"])
            self.refresh()

    def restock_product(self):
        p = self.get_selected()
        if not p: return
        qty = simpledialog.askinteger("Restock", f"Enter quantity to add to {p['name']}:", minvalue=1, parent=self)
        if qty:
            new_stock = int(p.get("stock",0)) + int(qty)
            db.update_product(p["id"], {"stock": new_stock})
            self.refresh()
            messagebox.showinfo("Restocked", f"New stock: {new_stock}")

    def sell_product(self):
        p = self.get_selected()
        if not p: return
        dlg = SellDialog(self, p)
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            qty, customer = dlg.result
            if p.get("stock",0) < qty:
                messagebox.showerror("Stock", "Not enough stock.")
                return
            new_stock = p.get("stock",0) - qty
            db.update_product(p["id"], {"stock": new_stock})
            tx_items = [{"product_id": p["id"], "name": p["name"], "qty": qty, "unit_price": p["price"]}]
            db.record_transaction(tx_items, qty * p["price"], customer=customer)
            self.refresh()
            messagebox.showinfo("Sold", f"Sold {qty} x {p['name']}")

    # -------------------- Manage Users --------------------
    def manage_users(self):
        dlg = ManageUsersDialog(self)
        self.wait_window(dlg)


# ---------------- Dialogs ----------------
class ProductDialog(tb.Toplevel):
    def __init__(self, master, product=None, title="Product"):
        super().__init__(master)
        self.result = None
        self.product = product or {}
        self.title(title)
        self.geometry("420x360")
        self.build()
        if product:
            self.fill(product)

    def build(self):
        frm = tb.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)
        labels = ["Name","Brand","Price","Stock","Expiry (YYYY-MM-DD)","Description"]
        self.vars = {}
        for i, lab in enumerate(labels):
            tb.Label(frm, text=lab).grid(row=i, column=0, sticky="w", pady=4)
            v = tb.Entry(frm, width=40)
            v.grid(row=i, column=1, pady=4)
            self.vars[lab] = v
        btnf = tb.Frame(frm)
        btnf.grid(row=len(labels), column=0, columnspan=2, pady=8)
        tb.Button(btnf, text="Save", bootstyle="success", command=self.on_save).pack(side="left", padx=4)
        tb.Button(btnf, text="Cancel", bootstyle="danger-outline", command=self.destroy).pack(side="left", padx=4)

    def fill(self, p):
        self.vars["Name"].insert(0, p.get("name",""))
        self.vars["Brand"].insert(0, p.get("brand",""))
        self.vars["Price"].insert(0, str(p.get("price","0")))
        self.vars["Stock"].insert(0, str(p.get("stock","0")))
        self.vars["Expiry (YYYY-MM-DD)"].insert(0, p.get("expiry",""))
        self.vars["Description"].insert(0, p.get("description",""))

    def on_save(self):
        try:
            data = {
                "name": self.vars["Name"].get().strip(),
                "brand": self.vars["Brand"].get().strip(),
                "price": float(self.vars["Price"].get() or 0),
                "stock": int(self.vars["Stock"].get() or 0),
                "expiry": self.vars["Expiry (YYYY-MM-DD)"].get().strip(),
                "description": self.vars["Description"].get().strip()
            }
        except Exception:
            messagebox.showerror("Validation", "Check numeric fields (price/stock).")
            return
        if not data["name"]:
            messagebox.showerror("Validation", "Name is required.")
            return
        self.result = data
        self.destroy()


class SellDialog(tb.Toplevel):
    def __init__(self, master, product):
        super().__init__(master)
        self.product = product
        self.result = None
        self.title("Sell Product")
        self.geometry("320x220")
        self.build()

    def build(self):
        frm = tb.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)
        tb.Label(frm, text=f"{self.product['name']} ({self.product['id']})", font=("Arial", 11, "bold")).pack(anchor="w")
        tb.Label(frm, text=f"Price: {self.product['price']:.2f} | Stock: {self.product.get('stock',0)}").pack(anchor="w", pady=(2,8))
        tb.Label(frm, text="Quantity:").pack(anchor="w")
        self.qty = tb.Entry(frm)
        self.qty.insert(0, "1")
        self.qty.pack(anchor="w")
        tb.Label(frm, text="Customer name (optional):").pack(anchor="w", pady=(8,0))
        self.cust = tb.Entry(frm)
        self.cust.insert(0, "Walk-in")
        self.cust.pack(anchor="w")
        btnf = tb.Frame(frm)
        btnf.pack(pady=10)
        tb.Button(btnf, text="Sell", bootstyle="success", command=self.on_sell).pack(side="left", padx=4)
        tb.Button(btnf, text="Cancel", bootstyle="danger-outline", command=self.destroy).pack(side="left", padx=4)

    def on_sell(self):
        try:
            q = int(self.qty.get())
        except Exception:
            messagebox.showerror("Error", "Quantity must be an integer")
            return
        c = self.cust.get().strip() or "Walk-in"
        if q <= 0:
            messagebox.showerror("Error", "Quantity must be > 0")
            return
        self.result = (q, c)
        self.destroy()


class ManageUsersDialog(tb.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Manage Users")
        self.geometry("520x360")
        self.configure(padx=10, pady=10)
        self.build()
        self.refresh()

    def build(self):
        top = tb.Frame(self, padding=8)
        top.pack(fill="x")
        tb.Button(top, text="Add Buyer", bootstyle="success-outline", command=self.add_user).pack(side="left", padx=4)
        tb.Button(top, text="Refresh", bootstyle="info-outline", command=self.refresh).pack(side="left", padx=4)

        cols = ("username","role","created")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=150, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=8)

    def refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        users = db.load_db().get("users", [])
        for u in users:
            self.tree.insert("", "end", values=(u.get("username"), u.get("role"), u.get("created","")))

    def add_user(self):
        dlg = AddUserDialog(self)
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            username, password = dlg.result
            ok = db.create_user(username, password, role="user")
            if not ok:
                messagebox.showerror("Error", "Username already exists.")
            else:
                messagebox.showinfo("Added", f"User {username} added.")
                self.refresh()


class AddUserDialog(tb.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Add Buyer")
        self.geometry("360x220")
        self.result = None
        frm = tb.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        tb.Label(frm, text="Username:").grid(row=0, column=0, sticky="w")
        self.username = tb.Entry(frm); self.username.grid(row=0, column=1, pady=6)
        tb.Label(frm, text="Password:").grid(row=1, column=0, sticky="w")
        self.password = tb.Entry(frm, show="*"); self.password.grid(row=1, column=1, pady=6)
        tb.Label(frm, text="Confirm:").grid(row=2, column=0, sticky="w")
        self.confirm = tb.Entry(frm, show="*"); self.confirm.grid(row=2, column=1, pady=6)
        btnf = tb.Frame(frm); btnf.grid(row=3, column=0, columnspan=2, pady=8)
        tb.Button(btnf, text="Add", bootstyle="success", command=self.on_add).pack(side="left", padx=4)
        tb.Button(btnf, text="Cancel", bootstyle="danger-outline", command=self.destroy).pack(side="left", padx=4)

    def on_add(self):
        u = self.username.get().strip(); p = self.password.get().strip(); c = self.confirm.get().strip()
        if not u or not p:
            messagebox.showerror("Validation", "All fields required")
            return
        if p != c:
            messagebox.showerror("Validation", "Passwords do not match")
            return
        self.result = (u, p)
        self.destroy()
