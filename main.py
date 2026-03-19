# main.pyABC
import tkinter as tk
from tkinter import messagebox
import db, admin_ui, buyer_ui

import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Use ttkbootstrap style
STYLE = tb.Style("minty")  # greenish medical theme

def open_role_login(role):
    login_win = tb.Toplevel()
    login_win.title(f"{role.title()} Login")
    login_win.geometry("380x260")
    login_win.configure(padx=10, pady=10, bg="#e6f9f0")

    frm = tb.Frame(login_win, padding=12)
    frm.pack(fill="both", expand=True)

    tb.Label(frm, text=f"{role.title()} Login", font=("Arial", 14, "bold"), bootstyle="success").grid(row=0, column=0, columnspan=2, pady=(0,8))
    tb.Label(frm, text="Username:").grid(row=1, column=0, sticky="w")
    username = tb.Entry(frm); username.grid(row=1, column=1, pady=4)
    tb.Label(frm, text="Password:").grid(row=2, column=0, sticky="w")
    password = tb.Entry(frm, show="*"); password.grid(row=2, column=1, pady=4)

    def attempt_login():
        uname = username.get().strip()
        pwd = password.get().strip()
        if not uname or not pwd:
            messagebox.showwarning("Login", "Enter username and password")
            return
        user = db.authenticate(uname, pwd)
        if not user or user.get("role") != role:
            messagebox.showerror("Login failed", "Invalid credentials or role")
            return
        login_win.destroy()
        root.withdraw()
        if role == "admin":
            admin_ui.AdminApp(root, user)
        else:
            buyer_ui.BuyerApp(root, user)

    tb.Button(frm, text="Login", bootstyle="success", width=20, command=attempt_login).grid(row=3, column=0, columnspan=2, pady=(10,0))

def open_register_dialog():
    reg = tb.Toplevel()
    reg.title("Register as Buyer")
    reg.geometry("380x260")
    reg.configure(padx=10, pady=10, bg="#e6f9f0")

    frm = tb.Frame(reg, padding=12)
    frm.pack(fill="both", expand=True)

    tb.Label(frm, text="Register as new buyer", font=("Arial", 12, "bold"), bootstyle="success").grid(row=0, column=0, columnspan=2, pady=(0,8))
    tb.Label(frm, text="Username:").grid(row=1, column=0, sticky="w")
    username = tb.Entry(frm); username.grid(row=1, column=1, pady=4)
    tb.Label(frm, text="Password:").grid(row=2, column=0, sticky="w")
    password = tb.Entry(frm, show="*"); password.grid(row=2, column=1, pady=4)
    tb.Label(frm, text="Confirm:").grid(row=3, column=0, sticky="w")
    confirm = tb.Entry(frm, show="*"); confirm.grid(row=3, column=1, pady=4)

    def register():
        u = username.get().strip(); p = password.get().strip(); c = confirm.get().strip()
        if not u or not p:
            messagebox.showerror("Register", "All fields required")
            return
        if p != c:
            messagebox.showerror("Register", "Passwords do not match")
            return
        ok = db.create_user(u, p, role="user")
        if not ok:
            messagebox.showerror("Register", "Username already exists")
            return
        messagebox.showinfo("Register", "Registration successful — you can now login.")
        reg.destroy()

    tb.Button(frm, text="Register", bootstyle="success", width=20, command=register).grid(row=4, column=0, columnspan=2, pady=(10,0))

def main():
    global root
    db.init_db_if_missing()
    root = tb.Window(themename="minty")  # greenish medical theme
    root.title("Pharmacy Management System")
    root.geometry("480x340")
    root.configure(padx=15, pady=15, bg="#e6f9f0")

    frm = tb.Frame(root, padding=18)
    frm.pack(fill="both", expand=True)

    tb.Label(frm, text="Pharmacy Management System", font=("Arial", 18, "bold"), bootstyle="success").pack(pady=(0,8))
    tb.Label(frm, text="Choose role to continue", font=("Arial", 11)).pack(pady=(0,8))

    tb.Button(frm, text="Login as Admin", bootstyle="success", width=32, command=lambda: open_role_login("admin")).pack(pady=6)
    tb.Button(frm, text="Login as Buyer", bootstyle="info", width=32, command=lambda: open_role_login("user")).pack(pady=6)
    tb.Button(frm, text="Register as Buyer", bootstyle="warning", width=32, command=open_register_dialog).pack(pady=6)

    root.mainloop()

if __name__ == "__main__":
    main()
        
