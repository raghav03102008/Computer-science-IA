Salon Management System

Overview
This project is a desktop salon management system built in Python. It provides a complete solution to manage daily salon operations including bookings, clients, staff, inventory, sales, and financial tracking. The application uses a graphical user interface (GUI) and integrates with a Microsoft Access database for data storage.

Features
The system includes a dashboard that displays key business metrics such as total clients, bookings for the day, and revenue figures. It also includes charts like 7-day revenue trends, booking status distribution, and service popularity.

The booking system allows users to create, edit, and cancel appointments. It prevents double-booking of hairdressers and keeps track of client, service, date, and time slot.

The client management section allows adding, editing, and deleting client records. Each client can store name, email, phone number, and a profile picture. A detailed overview is available showing visit history and total spending.

Hairdresser management allows storing employee details such as name, experience, notes, and profile images.

The product and inventory system allows adding and editing products, tracking stock levels, and performing bulk updates. Stock is automatically updated when sales are made.

The orders system records transactions, links them to clients, calculates totals, and updates inventory.

The financial system tracks revenue and expenses, calculates profit, shows monthly profit and loss, categorizes expenses, and allows exporting reports to Excel.

Technologies Used
The system is developed in Python using CustomTkinter and Tkinter for the graphical interface. Pillow is used for image processing, PyODBC for database connectivity, Matplotlib for charts, OpenPyXL for Excel export, and Microsoft Access as the database.

Important Requirements
The application only works on Windows because it depends on the Microsoft Access ODBC driver. A Microsoft Access database file (.accdb) is required to run the system. The database path is hardcoded in the code, so the file must either be placed in the specified location or the path must be updated manually. Without the database file, the program will not run.

Installation and Setup
First, install the required Python libraries using pip install customtkinter pillow pyodbc matplotlib openpyxl.
Next, install the Microsoft Access Database Engine to enable the ODBC driver.
Ensure the .accdb database file is available and correctly linked in the code by updating the DB_PATH variable if needed.
Finally, run the program using python backup.py.

Project Structure
The main application is contained in backup.py. The database is stored as a .accdb file, and additional assets such as icons are stored in an Icons folder.

How It Works
The program connects to the Access database using PyODBC. SQL queries are used to retrieve, insert, and update data. The GUI updates dynamically based on the data in the database. Charts are generated using Matplotlib, and financial reports are exported using OpenPyXL.

Limitations
The system only works on Windows due to the Access dependency. It requires a local database file and uses hardcoded file paths for the database and icons. There is no authentication system, and the application is not web-based.

Future Improvements
Possible improvements include making the database path configurable, adding user authentication, migrating to a more scalable database such as MySQL or SQL Server, creating a cloud-based version, and making the application cross-platform.
