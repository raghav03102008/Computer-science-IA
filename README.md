# Salon Management System

## Overview

This project is a desktop salon management system built in Python. It provides a complete solution to manage daily salon operations including bookings, clients, staff, inventory, sales, and financial tracking. The application uses a graphical user interface (GUI) and integrates with a Microsoft Access database for data storage.

---

## ⚠️ Setup Instructions (Read Before Running)

> **Follow these steps exactly. The application will not run without the database file.**

### Step 1 — Place both files in the same folder

Put the executable and the database file **in the same folder** on your computer. For example:

```
C:\SalonApp\
    SalonManagementSystem.exe
    Barber appointment system.accdb
```

Both files must be in the same directory. If they are separated, the app will prompt you to locate the database manually (see Step 3).

### Step 2 — Install the Microsoft Access Database Engine

The app requires the Microsoft Access ODBC driver to read the `.accdb` database file.

1. Go to: https://www.microsoft.com/en-us/download/details.aspx?id=54920
2. Download and install the **Microsoft Access Database Engine 2016 Redistributable**
3. Restart your computer after installation

> **This step is required even if you have Microsoft Office installed.** Skip it and the app will fail to open the database.

### Step 3 — Run the application

Double-click **`SalonManagementSystem.exe`** to launch the app.

- If the database is found automatically (same folder as the exe), the app opens normally.
- **If the database is not found**, a file picker will appear asking you to locate the `.accdb` file. Navigate to where you saved it, select it, and click Open. The app will then connect and launch.

### Step 4 — Changing the database at runtime

If you ever need to switch to a different database file while the app is running, use the **"🗄 Change Database"** button at the bottom of the left sidebar. This lets you browse for and connect to a different `.accdb` file without restarting the app.

---

## Features

The system includes a **dashboard** that displays key business metrics such as total clients, bookings for the day, and revenue figures, along with charts for 7-day revenue trends, booking status distribution, and service popularity.

The **booking system** allows users to create, edit, and cancel appointments. It prevents double-booking of hairdressers and tracks client, service, date, and time slot.

**Client management** allows adding, editing, and deleting client records. Each client can store a name, email, phone number, and profile picture. A detailed overview shows visit history and total spending.

**Hairdresser management** stores employee details such as name, experience, notes, and profile images.

The **product and inventory system** allows adding and editing products, tracking stock levels, and performing bulk updates. Stock is automatically updated when sales are made.

The **orders system** records transactions, links them to clients, calculates totals, and updates inventory.

The **financial system** tracks revenue and expenses, calculates profit, shows monthly profit and loss, categorizes expenses, and allows exporting reports to Excel.

---

## Technologies Used

- **Python** — core language
- **CustomTkinter / Tkinter** — graphical user interface
- **Pillow** — image processing
- **PyODBC** — database connectivity
- **Matplotlib** — charts and graphs
- **OpenPyXL** — Excel export
- **Microsoft Access (.accdb)** — database

---

## Important Requirements

- Windows only — the app depends on the Microsoft Access ODBC driver, which is Windows-exclusive.
- The `.accdb` database file must be present. If it is not in the same folder as the exe, the app will prompt you to locate it on first launch.

---

## Project Structure

```
SalonManagementSystem.exe       ← Main application
Barber appointment system.accdb ← Database (must be in same folder)
Icons/                          ← Application icons (bundled inside exe)
dashboardtesting.py             ← Source code
```

---

## How It Works

The program connects to the Access database using PyODBC. SQL queries retrieve, insert, and update records. The GUI updates dynamically based on database contents. Charts are generated with Matplotlib, and financial reports are exported using OpenPyXL.

---

## Limitations

- Windows only due to the Microsoft Access ODBC dependency.
- No user authentication system.
- Not web-based; requires local installation.

---

## Future Improvements

- Migrate to a more scalable database (MySQL, SQL Server)
- Add user authentication and role-based access
- Build a cloud-based or web version
- Make the application cross-platform
