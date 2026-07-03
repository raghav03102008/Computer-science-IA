# Salon Management System

A desktop app for managing a salon's day-to-day stuff, bookings, clients, staff, inventory, sales, the works. Built in Python with a GUI, backed by a Microsoft Access database.

Made for Stardance Hack Club.

---

## ⚠️ Before You Run It

The app **will not open** unless you do these in order.

### 1. Keep both files together

Put the .exe and the .accdb file in the same folder:

```
C:\SalonApp\
    SalonManagementSystem.exe
    Barber appointment system.accdb
```

If they're not in the same folder, the app will ask you to find the database manually, see step 3.

### 2. Install the Access Database Engine

You need this even if you already have Microsoft Office. Without it, the app can't talk to the .accdb file.

1. Download it here: https://www.microsoft.com/en-us/download/details.aspx?id=54920
2. Install the **Microsoft Access Database Engine 2016 Redistributable**
3. Restart your PC after installing

### 3. Launch it

Double-click `SalonManagementSystem.exe`.

- Found the database automatically? Great, it just opens.
- Didn't find it? A file picker pops up, just browse to the .accdb file and select it.

### 4. Switching databases later

There's a **"🗄 Change Database"** button at the bottom of the sidebar if you ever need to point the app at a different .accdb file without restarting.

---

## What It Actually Does

**Dashboard**, total clients, today's bookings, revenue, plus charts for the last 7 days of revenue, booking status breakdown, and which services are most popular.

**Bookings**, create, edit, cancel appointments. Won't let you double-book a hairdresser.

**Clients**, add, edit, delete records, store name, email, phone, profile pic. You can pull up a client and see their whole visit history and how much they've spent.

**Hairdressers**, track staff details, experience, notes, photos.

**Inventory**, add, edit products, track stock, bulk updates. Stock drops automatically when something's sold.

**Orders**, records the transaction, links it to the client, totals it up, updates stock.

**Finances**, revenue vs expenses, profit, monthly P&L, expense categories, and you can export everything to Excel.

---

## Built With

- Python
- CustomTkinter / Tkinter for the UI
- Pillow for images
- PyODBC for the database connection
- Matplotlib for the charts
- OpenPyXL for Excel exports
- Microsoft Access (.accdb) as the database

---

## Heads Up

- **Windows only**, the Access ODBC driver just doesn't exist for Mac/Linux.
- No login system yet, anyone with the app can access everything.
- Local only, not web-based.

---

## Project Files

```
SalonManagementSystem.exe       ← the app
Barber appointment system.accdb ← the database (needs to sit next to the exe)
Icons/                          ← bundled inside the exe
dashboardtesting.py             ← source code
```

---

## What's Next

If I keep building this out:
- Swap Access for something more scalable, like MySQL
- Add proper logins and permissions
- Maybe a web version eventually
- Get it working cross-platform
