from customtkinter import *
from PIL import Image, ImageDraw
import pyodbc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import os

from tkinter import filedialog
from openpyxl import Workbook
from openpyxl.styles import Font
# ═══════════════════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════════════════

DB_PATH = r"C:\Users\ragha\Documents\COmputer Science IA\Barber appointment system.accdb"
conn = pyodbc.connect(
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={DB_PATH};"
)
cursor = conn.cursor()

# ═══════════════════════════════════════════════════════════════
#  DESIGN TOKENS  — Soft Dark + Warm Gold
# ═══════════════════════════════════════════════════════════════

C_BG        = "#1a1a1a"
C_SURFACE   = "#242424"
C_SURFACE2  = "#2c2c2c"
C_SIDEBAR   = "#1e1e1e"
C_GOLD      = "#c9a84c"
C_GOLD_DARK = "#a8893a"
C_SUCCESS   = "#4caf7d"
C_DANGER    = "#e05252"
C_WARNING   = "#e0993a"
C_MUTED     = "#888888"
C_TEXT      = "#f0f0f0"
C_TEXT_DIM  = "#aaaaaa"
C_BORDER    = "#333333"
C_CHART_BG  = "#1e1e1e"

FONT_TITLE   = ("Inter", 22, "bold")
FONT_SECTION = ("Inter", 16, "bold")
FONT_CARD_VAL= ("Inter", 24, "bold")
FONT_LABEL   = ("Inter", 11)
FONT_BODY    = ("Inter", 13)
FONT_BOLD    = ("Inter", 13, "bold")
FONT_SMALL   = ("Inter", 11)

RADIUS = 14
PAD    = 16

ICON_DIR = r"C:\Users\ragha\Documents\COmputer Science IA\Icons"

ICON_PATHS = {
    "dashboard": os.path.join(ICON_DIR, "dashboard.png"),
    "hairdressers": os.path.join(ICON_DIR, "haircut.png"),
    "clients": os.path.join(ICON_DIR, "customer.png"),
    "products": os.path.join(ICON_DIR, "toiletries.png"),
    "schedule": os.path.join(ICON_DIR, "calendar.png"),
    "orders": os.path.join(ICON_DIR, "orders.png"),
    "finance": os.path.join(ICON_DIR, "orders.png"),   # reuse orders icon as fallback
    "plus": os.path.join(ICON_DIR, "plus.png"),
}

# ═══════════════════════════════════════════════════════════════
#  GLOBAL STATE
# ═══════════════════════════════════════════════════════════════

product_tile_refs      = {}
products_container     = None
selected_hairdresser_id   = None
selected_hairdresser_name = ""
client_view_mode       = "cards"
client_search_var      = None
hairdresser_view_mode  = "cards"
hairdresser_search_var = None

# ═══════════════════════════════════════════════════════════════
#  GENERIC HELPERS
# ═══════════════════════════════════════════════════════════════

def clear_frame(frame):
    for w in frame.winfo_children():
        w.destroy()

def safe_int(v, default=0):
    try: return int(v)
    except: return default

def safe_float(v, default=0.0):
    try: return float(v)
    except: return default

def safe_text(v, fallback="—"):
    return str(v) if v not in (None, "") else fallback

def format_date(v, fmt="%Y-%m-%d"):
    return v.strftime(fmt) if v else ""

def format_slot(v):
    return v.strftime("%I:%M %p").lstrip("0") if v else ""

def load_icon(key, size=(18, 18)):
    try:
        img = Image.open(ICON_PATHS[key]).convert("RGBA")
        return CTkImage(light_image=img, dark_image=img, size=size)
    except:
        return None

def build_avatar(path, size=(90, 90), circle=True):
    try:
        if path and str(path).strip():
            img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
        else:
            raise ValueError()
    except:
        img = Image.new("RGBA", size, (60, 60, 60, 255))
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    if circle:
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
    else:
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius=16, fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return CTkImage(light_image=out, dark_image=out, size=size)

def build_plus_icon(size=(70, 70)):
    try:
        img = Image.open(ICON_PATHS["plus"]).convert("RGBA")
        return CTkImage(light_image=img, dark_image=img, size=size)
    except:
        return None
    
def bind_scroll_fix(inner_scroll):
    def _on_mousewheel(event):
        inner_scroll._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _bind(e):
        inner_scroll.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind(e):
        inner_scroll.unbind_all("<MouseWheel>")

    inner_scroll.bind("<Enter>", _bind)
    inner_scroll.bind("<Leave>", _unbind)

def add_commission_expense(booking_id):
    try:
        # get booking + service info
        cursor.execute("""
            SELECT b.BookingID, b.[Date], s.Price, s.ServiceName
            FROM Bookings b
            INNER JOIN Services s ON b.ServiceID = s.ServiceID
            WHERE b.BookingID = ?
        """, (booking_id,))
        row = cursor.fetchone()

        if not row:
            return

        bid, date_val, price, service_name = row

        # calculate 20%
        commission = round(float(price) * 0.20, 2)

        note_text = f"Commission for booking {bid}"

        # prevent duplicate
        cursor.execute("""
            SELECT COUNT(*)
            FROM Expenses
            WHERE Notes = ?
        """, (note_text,))
        if cursor.fetchone()[0] > 0:
            return

        # insert into YOUR schema
        cursor.execute("""
            INSERT INTO Expenses (Title, Amount, Category, DateTime, Notes)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"Commission - {service_name}",
            commission,
            "Wages / Salaries",
            date_val,
            note_text
        ))

        conn.commit()

    except Exception as e:
        print("Commission error:", e)

def export_pl_excel():
    path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")],
        initialfile="profit_and_loss.xlsx"
    )
    if not path:
        return

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "P&L Summary"

    rev = db_total_revenue_alltime()
    costs = db_total_costs_alltime()
    svc_m, prod_m = db_revenue_by_category()

    try:
        cursor.execute("SELECT SUM(Amount) FROM Expenses WHERE Month(DateTime)=Month(Date()) AND Year(DateTime)=Year(Date())")
        month_costs = safe_float(cursor.fetchone()[0])
    except:
        month_costs = 0.0

    ws1["A1"] = "Profit & Loss Summary"
    ws1["A1"].font = Font(bold=True, size=14)

    ws1["A3"] = "Total Revenue (All Time)"
    ws1["B3"] = rev

    ws1["A4"] = "Total Costs (All Time)"
    ws1["B4"] = costs

    ws1["A5"] = "Net Profit (All Time)"
    ws1["B5"] = "=B3-B4"

    ws1["A6"] = "Profit Margin"
    ws1["B6"] = "=IF(B3=0,0,B5/B3)"

    ws1["A8"] = "Service Revenue (This Month)"
    ws1["B8"] = svc_m

    ws1["A9"] = "Product Revenue (This Month)"
    ws1["B9"] = prod_m

    ws1["A10"] = "Costs (This Month)"
    ws1["B10"] = month_costs

    ws1["A11"] = "Net Profit (This Month)"
    ws1["B11"] = "=SUM(B8:B9)-B10"

    for cell in ["B3","B4","B5","B8","B9","B10","B11"]:
        ws1[cell].number_format = '$#,##0.00'
    ws1["B6"].number_format = '0.00%'

    ws1.column_dimensions["A"].width = 28
    ws1.column_dimensions["B"].width = 18

    ws2 = wb.create_sheet("Monthly P&L")
    ws2["A1"] = "Month"
    ws2["B1"] = "Revenue"
    ws2["C1"] = "Costs"
    ws2["D1"] = "Net Profit"

    for cell in ["A1", "B1", "C1", "D1"]:
        ws2[cell].font = Font(bold=True)

    data = db_monthly_pl(12)

    row = 2
    for label, revenue, cost in data:
        ws2[f"A{row}"] = label
        ws2[f"B{row}"] = revenue
        ws2[f"C{row}"] = cost
        ws2[f"D{row}"] = f"=B{row}-C{row}"
        ws2[f"B{row}"].number_format = '$#,##0.00'
        ws2[f"C{row}"].number_format = '$#,##0.00'
        ws2[f"D{row}"].number_format = '$#,##0.00'
        row += 1

    ws2.column_dimensions["A"].width = 16
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 14
    ws2.column_dimensions["D"].width = 14

    wb.save(path)

# ─── Reusable UI primitives ──────────────────────────────────

def section_header(parent, title, btn_label=None, btn_cmd=None, pady=(0, 12)):
    """Standard page/section header: title left, optional CTA right."""
    row = CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=PAD, pady=pady)
    CTkLabel(row, text=title, font=FONT_TITLE, text_color=C_TEXT).pack(side="left")
    if btn_label:
        _gold_btn(row, btn_label, btn_cmd, width=140).pack(side="right")
    return row

def _gold_btn(parent, text, command=None, width=120, height=34, danger=False):
    fg   = C_DANGER if danger else C_GOLD
    hover= "#c04040" if danger else C_GOLD_DARK
    return CTkButton(
        parent, text=text, command=command,
        width=width, height=height,
        fg_color=fg, hover_color=hover,
        text_color="#1a1a1a" if not danger else C_TEXT,
        font=FONT_BOLD, corner_radius=8
    )

def _ghost_btn(parent, text, command=None, width=100, height=34):
    return CTkButton(
        parent, text=text, command=command,
        width=width, height=height,
        fg_color="transparent", border_color=C_BORDER, border_width=1,
        text_color=C_TEXT_DIM, hover_color=C_SURFACE2,
        font=FONT_BODY, corner_radius=8
    )

def card_frame(parent, **kwargs):
    return CTkFrame(parent, fg_color=C_SURFACE, corner_radius=RADIUS, **kwargs)

def divider(parent):
    CTkFrame(parent, fg_color=C_BORDER, height=1).pack(fill="x", padx=PAD, pady=4)

def kpi_card(parent, title, value, subtitle="", accent=C_GOLD, row=0, col=0):
    card = CTkFrame(parent, fg_color=C_SURFACE, corner_radius=RADIUS)
    card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
    # accent top strip
    CTkFrame(card, fg_color=accent, height=3, corner_radius=2).pack(fill="x", padx=0, pady=(0, 0))
    CTkLabel(card, text=title, font=FONT_SMALL, text_color=C_MUTED).pack(anchor="w", padx=PAD, pady=(10, 2))
    val_lbl = CTkLabel(card, text=value, font=FONT_CARD_VAL, text_color=C_TEXT)
    val_lbl.pack(anchor="w", padx=PAD, pady=(0, 2))
    if subtitle:
        CTkLabel(card, text=subtitle, font=FONT_SMALL, text_color=C_MUTED).pack(anchor="w", padx=PAD, pady=(0, 10))
    else:
        CTkFrame(card, fg_color="transparent", height=10).pack()
    return card, val_lbl

def render_table_headers(parent, headers, weights=None):
    for col, header in enumerate(headers):
        w = weights[col] if weights else 1
        CTkLabel(parent, text=header, font=FONT_BOLD, text_color=C_MUTED).grid(
            row=0, column=col, padx=12, pady=(10, 8), sticky="w")
        parent.grid_columnconfigure(col, weight=w)
    CTkFrame(parent, fg_color=C_BORDER, height=1).grid(
        row=1, column=0, columnspan=len(headers), sticky="ew", padx=8, pady=0)

def table_cell(parent, text, row, col, color=C_TEXT, bold=False, wraplength=0):
    font = FONT_BOLD if bold else FONT_BODY
    kw = {"wraplength": wraplength} if wraplength else {}
    CTkLabel(parent, text=text, font=font, text_color=color, **kw).grid(
        row=row+2, column=col, padx=12, pady=7, sticky="w")

def status_badge(parent, text, row, col):
    colors = {"Completed": C_SUCCESS, "Upcoming": C_WARNING, "Canceled": C_DANGER}
    color = colors.get(text, C_MUTED)
    badge = CTkFrame(parent, fg_color=color, corner_radius=8)
    badge.grid(row=row+2, column=col, padx=12, pady=7, sticky="w")
    CTkLabel(badge, text=text, font=FONT_SMALL, text_color="white").pack(padx=8, pady=2)

def empty_state(parent, text, colspan):
    CTkLabel(parent, text=text, font=FONT_BODY, text_color=C_MUTED).grid(
        row=2, column=0, columnspan=colspan, pady=24)

def labeled_entry(parent, label, row, col, width=230, placeholder=None):
    CTkLabel(parent, text=label, font=FONT_SMALL, text_color=C_TEXT_DIM).grid(
        row=row, column=col, sticky="w", padx=PAD, pady=(10, 3))
    kw = {"placeholder_text": placeholder} if placeholder else {}
    e = CTkEntry(parent, width=width, fg_color=C_SURFACE2, border_color=C_BORDER,
                 text_color=C_TEXT, placeholder_text_color=C_MUTED, **kw)
    e.grid(row=row+1, column=col, padx=PAD, pady=(0, PAD))
    return e

# ─── Overlay modal ───────────────────────────────────────────

def overlay_modal(parent, title, width=680, height=500):
    overlay = CTkFrame(parent, fg_color="#000000")
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    overlay.lift()
    panel = CTkFrame(overlay, fg_color=C_SURFACE, corner_radius=18, width=width, height=height)
    panel.place(relx=0.5, rely=0.5, anchor="center")
    panel.grid_columnconfigure((0, 1), weight=1)
    # gold title bar
    title_bar = CTkFrame(panel, fg_color=C_SURFACE2, corner_radius=0, height=56)
    title_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
    CTkLabel(title_bar, text=title, font=FONT_SECTION, text_color=C_GOLD).pack(side="left", padx=PAD)
    CTkButton(title_bar, text="✕", width=36, height=36, fg_color="transparent",
              hover_color=C_DANGER, text_color=C_TEXT_DIM, command=overlay.destroy).pack(side="right", padx=8)
    err = CTkLabel(panel, text="", text_color=C_DANGER, font=FONT_SMALL)
    err.grid(row=9, column=0, columnspan=2, pady=(0, 4))
    return overlay, panel, err

def modal_buttons(panel, overlay, on_save, on_delete=None, save_text="Save", delete_text="Delete"):
    bf = CTkFrame(panel, fg_color="transparent")
    bf.grid(row=8, column=0, columnspan=2, pady=(16, 8))
    _gold_btn(bf, save_text, on_save, width=160).pack(side="left", padx=8)
    if on_delete:
        _ghost_btn(bf, delete_text, on_delete, width=140).pack(side="left", padx=8)
    _ghost_btn(bf, "Close", overlay.destroy, width=100).pack(side="left", padx=8)

# ═══════════════════════════════════════════════════════════════
#  CHART HELPERS
# ═══════════════════════════════════════════════════════════════

def _chart_fig(w=6, h=3.4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(C_CHART_BG)
    ax.set_facecolor(C_CHART_BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=C_MUTED)
    ax.title.set_color(C_TEXT)
    return fig, ax

def embed_chart(fig, parent):
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    w = canvas.get_tk_widget()
    w.configure(bg=C_CHART_BG, highlightthickness=0)
    w.pack(fill="both", expand=True)
    plt.close(fig)

# ═══════════════════════════════════════════════════════════════
#  DATA — DASHBOARD
# ═══════════════════════════════════════════════════════════════

def db_total_clients():
    cursor.execute("SELECT COUNT(*) FROM Clients")
    return safe_int(cursor.fetchone()[0])

def db_bookings_today():
    cursor.execute("SELECT COUNT(*) FROM Bookings WHERE DateValue([Date])=Date() AND Canceled=False")
    return safe_int(cursor.fetchone()[0])

def db_revenue_today():
    cursor.execute("""
        SELECT SUM(Services.Price) FROM Bookings
        INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
        WHERE DateValue(Bookings.[Date])=Date() AND Bookings.IsCompleted=True
    """)
    return safe_float(cursor.fetchone()[0])

def db_monthly_revenue():
    cursor.execute("""
        SELECT SUM(Services.Price) FROM Bookings
        INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
        WHERE Month(Bookings.[Date])=Month(Date()) AND Year(Bookings.[Date])=Year(Date())
          AND Bookings.IsCompleted=True AND Bookings.Canceled=False
    """)
    svc = safe_float(cursor.fetchone()[0])
    cursor.execute("""
        SELECT SUM(TotalAmount) FROM Orders
        WHERE Month(OrderDate)=Month(Date()) AND Year(OrderDate)=Year(Date())
    """)
    prod = safe_float(cursor.fetchone()[0])
    return svc + prod

def db_cancel_rate():
    cursor.execute("SELECT COUNT(*) FROM Bookings WHERE Month([Date])=Month(Date()) AND Year([Date])=Year(Date())")
    tot = safe_int(cursor.fetchone()[0])
    if not tot: return 0.0
    cursor.execute("SELECT COUNT(*) FROM Bookings WHERE Month([Date])=Month(Date()) AND Year([Date])=Year(Date()) AND Canceled=True")
    return round(safe_int(cursor.fetchone()[0]) / tot * 100, 1)

def db_avg_service():
    cursor.execute("""
        SELECT AVG(Services.Price) FROM Bookings
        INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
        WHERE Bookings.IsCompleted=True AND Bookings.Canceled=False
    """)
    return safe_float(cursor.fetchone()[0])

def db_busiest_day():
    cursor.execute("""
        SELECT Weekday([Date],2) AS wd, COUNT(*) FROM Bookings
        WHERE DateValue([Date])>=Date()-(Weekday(Date(),2)-1)
          AND DateValue([Date])<Date()+(8-Weekday(Date(),2))
          AND Canceled=False
        GROUP BY Weekday([Date],2) ORDER BY COUNT(*) DESC
    """)
    row = cursor.fetchone()
    days = {1:"Monday",2:"Tuesday",3:"Wednesday",4:"Thursday",5:"Friday",6:"Saturday",7:"Sunday"}
    return days.get(safe_int(row[0]) if row else 0, "—")

def db_top_hairdresser():
    cursor.execute("""
        SELECT TOP 1 Hairdressers.HairdresserName FROM Bookings
        INNER JOIN Hairdressers ON Bookings.HairdresserID=Hairdressers.HairdresserID
        WHERE Month(Bookings.[Date])=Month(Date()) AND Year(Bookings.[Date])=Year(Date())
          AND Bookings.IsCompleted=True AND Bookings.Canceled=False
        GROUP BY Hairdressers.HairdresserName ORDER BY COUNT(*) DESC
    """)
    r = cursor.fetchone(); return r[0] if r else "—"

def db_top_service():
    cursor.execute("""
        SELECT TOP 1 Services.ServiceName FROM Bookings
        INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
        WHERE Month(Bookings.[Date])=Month(Date()) AND Year(Bookings.[Date])=Year(Date())
          AND Bookings.Canceled=False
        GROUP BY Services.ServiceName ORDER BY COUNT(*) DESC
    """)
    r = cursor.fetchone(); return r[0] if r else "—"

def db_low_stock(threshold=5):
    cursor.execute("SELECT ProductName, StockRemaining FROM Products WHERE StockRemaining<=? ORDER BY StockRemaining", (threshold,))
    return cursor.fetchall()

def db_7day_revenue():
    today = datetime.today().date()
    labels, svc_rev, prod_rev = [], [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        labels.append(d.strftime("%a"))
        cursor.execute("""
            SELECT SUM(Services.Price) FROM Bookings
            INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
            WHERE DateValue(Bookings.[Date])=? AND Bookings.IsCompleted=True AND Bookings.Canceled=False
        """, (ds,))
        svc_rev.append(safe_float(cursor.fetchone()[0]))
        cursor.execute("SELECT SUM(TotalAmount) FROM Orders WHERE DateValue(OrderDate)=?", (ds,))
        prod_rev.append(safe_float(cursor.fetchone()[0]))
    return labels, svc_rev, prod_rev

def db_booking_statuses():
    cursor.execute("""
        SELECT SUM(IIf(Canceled=True,1,0)), SUM(IIf(IsCompleted=True AND Canceled=False,1,0)),
               SUM(IIf(IsCompleted=False AND Canceled=False,1,0))
        FROM Bookings WHERE Month([Date])=Month(Date()) AND Year([Date])=Year(Date())
    """)
    r = cursor.fetchone()
    return safe_int(r[2]), safe_int(r[1]), safe_int(r[0])  # upcoming, completed, canceled

def db_monthly_services():
    cursor.execute("""
        SELECT Services.ServiceName, COUNT(*) FROM Bookings
        INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
        WHERE Month(Bookings.[Date])=Month(Date()) AND Year(Bookings.[Date])=Year(Date())
          AND Bookings.Canceled=False
        GROUP BY Services.ServiceName ORDER BY COUNT(*) DESC
    """)
    return cursor.fetchall()

# ═══════════════════════════════════════════════════════════════
#  DATA — BOOKINGS
# ═══════════════════════════════════════════════════════════════

_BOOKING_SELECT = """
    SELECT Bookings.BookingID, Clients.ClientName, Services.ServiceName,
           Bookings.[Date], SlotData.Timings, Hairdressers.HairdresserName,
           IIf(Bookings.Canceled=True,'Canceled',IIf(Bookings.IsCompleted=True,'Completed','Upcoming')) AS Status
    FROM (((Bookings
    INNER JOIN Clients     ON Bookings.ClientID=Clients.ClientID)
    INNER JOIN Services    ON Bookings.ServiceID=Services.ServiceID)
    INNER JOIN Hairdressers ON Bookings.HairdresserID=Hairdressers.HairdresserID)
    INNER JOIN SlotData    ON Bookings.Slot=SlotData.ID
"""

def db_upcoming_bookings():
    cursor.execute(_BOOKING_SELECT +
        "WHERE Bookings.Canceled=False AND DateValue(Bookings.[Date])>=Date() AND DateValue(Bookings.[Date])<=Date()+1 "
        "ORDER BY Bookings.[Date],Bookings.Slot")
    return cursor.fetchall()

def db_all_bookings():
    cursor.execute(_BOOKING_SELECT +
        "WHERE Bookings.Canceled=False ORDER BY Bookings.[Date],Bookings.Slot")
    return cursor.fetchall()

def db_canceled_bookings():
    cursor.execute("""
        SELECT Bookings.BookingID, Clients.ClientName, Services.ServiceName,
               Bookings.[Date], SlotData.Timings, Hairdressers.HairdresserName, 'Canceled'
        FROM (((Bookings
        INNER JOIN Clients ON Bookings.ClientID=Clients.ClientID)
        INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID)
        INNER JOIN Hairdressers ON Bookings.HairdresserID=Hairdressers.HairdresserID)
        INNER JOIN SlotData ON Bookings.Slot=SlotData.ID
        WHERE Bookings.Canceled=True ORDER BY Bookings.[Date],Bookings.Slot
    """)
    return cursor.fetchall()

def db_booking_refs():
    cursor.execute("SELECT ClientID,ClientName FROM Clients ORDER BY ClientName")
    client_map = {r[1]:r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT HairdresserID,HairdresserName FROM Hairdressers ORDER BY HairdresserName")
    hair_map = {r[1]:r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT ServiceID,ServiceName FROM Services ORDER BY ServiceName")
    svc_map = {r[1]:r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT ID,Timings FROM SlotData ORDER BY Timings")
    slot_rows = cursor.fetchall()
    slot_map = {r[1].strftime('%H:%M'):r[0] for r in slot_rows}
    slot_rev  = {v:k for k,v in slot_map.items()}
    return client_map, hair_map, svc_map, slot_map, slot_rev

# ═══════════════════════════════════════════════════════════════
#  DATA — FINANCIALS
# ═══════════════════════════════════════════════════════════════

EXPENSE_CATS = ["Wages / Salaries", "Rent & Utilities", "Product Restocking", "Equipment & Supplies", "Other"]

def db_total_revenue_alltime():
    cursor.execute("""
        SELECT SUM(Services.Price) FROM Bookings
        INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
        WHERE Bookings.IsCompleted=True AND Bookings.Canceled=False
    """)
    svc = safe_float(cursor.fetchone()[0])
    cursor.execute("SELECT SUM(TotalAmount) FROM Orders")
    prod = safe_float(cursor.fetchone()[0])
    return svc + prod

def db_total_costs_alltime():
    try:
        cursor.execute("SELECT SUM(Amount) FROM Expenses")
        return safe_float(cursor.fetchone()[0])
    except:
        return 0.0

def db_monthly_pl(months=6):
    """Returns list of (label, revenue, costs) for last N months."""
    results = []
    today = datetime.today()
    for i in range(months-1, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year - ((today.month - i - 1) // 12) if (today.month - i - 1) >= 0 else today.year - 1
        label = datetime(y, m, 1).strftime("%b '%y")
        cursor.execute("""
            SELECT SUM(Services.Price) FROM Bookings
            INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
            WHERE Month(Bookings.[Date])=? AND Year(Bookings.[Date])=?
              AND Bookings.IsCompleted=True AND Bookings.Canceled=False
        """, (m, y))
        svc = safe_float(cursor.fetchone()[0])
        cursor.execute("SELECT SUM(TotalAmount) FROM Orders WHERE Month(OrderDate)=? AND Year(OrderDate)=?", (m, y))
        prod = safe_float(cursor.fetchone()[0])
        try:
            cursor.execute("SELECT SUM(Amount) FROM Expenses WHERE Month(DateTime)=? AND Year(DateTime)=?", (m, y))
            costs = safe_float(cursor.fetchone()[0])
        except:
            costs = 0.0
        results.append((label, svc+prod, costs))
    return results

def db_expenses(search="", category="All"):
    try:
        base = "SELECT ExpenseID,Category,Title,Amount,DateTime,Notes FROM Expenses"
        conds, params = [], []
        if category and category != "All":
            conds.append("Category=?"); params.append(category)
        if search.strip():
            conds.append("(Title LIKE ? OR Category LIKE ?)")
            params += [f"%{search}%", f"%{search}%"]
        q = base + (" WHERE " + " AND ".join(conds) if conds else "") + " ORDER BY DateTime DESC"
        cursor.execute(q, params)
        return cursor.fetchall()
    except Exception as e:
        print("DB EXPENSES ERROR:", e)
        return []

def db_revenue_by_category():
    """Returns service revenue and product revenue totals for current month."""
    cursor.execute("""
        SELECT SUM(Services.Price) FROM Bookings
        INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID
        WHERE Month(Bookings.[Date])=Month(Date()) AND Year(Bookings.[Date])=Year(Date())
          AND Bookings.IsCompleted=True AND Bookings.Canceled=False
    """)
    svc = safe_float(cursor.fetchone()[0])
    cursor.execute("SELECT SUM(TotalAmount) FROM Orders WHERE Month(OrderDate)=Month(Date()) AND Year(OrderDate)=Year(Date())")
    prod = safe_float(cursor.fetchone()[0])
    return svc, prod

# ═══════════════════════════════════════════════════════════════
#  APP SETUP
# ═══════════════════════════════════════════════════════════════

set_appearance_mode("dark")
set_default_color_theme("dark-blue")

app = CTk()
app.title("Salon Manager")
app.geometry("1280x780")
app.configure(fg_color=C_BG)
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════

sidebar = CTkFrame(app, width=230, fg_color=C_SIDEBAR, corner_radius=0)
sidebar.grid(row=0, column=0, sticky="ns")
sidebar.grid_propagate(False)

CTkLabel(sidebar, text="✂  Salon", font=("Inter", 20, "bold"),
         text_color=C_GOLD).pack(pady=(28, 24), padx=20, anchor="w")

CTkFrame(sidebar, fg_color=C_BORDER, height=1).pack(fill="x", padx=16, pady=(0, 16))

_active_tab_btns = {}
_active_tab = [None]

def _sidebar_btn(label, icon_key, tab_name):
    icon = load_icon(icon_key, (17, 17))
    btn = CTkButton(
        sidebar, text=f"  {label}", image=icon, compound="left", anchor="w",
        width=198, height=40, corner_radius=10,
        fg_color="transparent", hover_color=C_SURFACE,
        text_color=C_TEXT_DIM, font=FONT_BODY,
        command=lambda: show_content(tab_name)
    )
    btn.pack(padx=16, pady=3)
    _active_tab_btns[tab_name] = btn
    return btn

_sidebar_btn("Dashboard",     "dashboard",    "Dashboard")
_sidebar_btn("Hairdressers",  "hairdressers", "Hairdressers")
_sidebar_btn("Clients",       "clients",      "Clients")
_sidebar_btn("Products",      "products",     "Products")
_sidebar_btn("Schedule",      "schedule",     "Schedule")
_sidebar_btn("Orders",        "orders",       "Orders")
_sidebar_btn("Financials",    "finance",      "Financials")

def _set_active_tab(name):
    for k, b in _active_tab_btns.items():
        if k == name:
            b.configure(fg_color=C_SURFACE2, text_color=C_GOLD)
        else:
            b.configure(fg_color="transparent", text_color=C_TEXT_DIM)
    _active_tab[0] = name

# ═══════════════════════════════════════════════════════════════
#  CONTENT HOLDER
# ═══════════════════════════════════════════════════════════════

holder = CTkFrame(app, fg_color=C_BG, corner_radius=0)
holder.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
holder.grid_rowconfigure(0, weight=1)
holder.grid_columnconfigure(0, weight=1)

def _make_tab():
    f = CTkFrame(holder, fg_color=C_BG, corner_radius=0)
    f.grid_rowconfigure(0, weight=1)
    f.grid_columnconfigure(0, weight=1)
    return f

dashboard_frame         = _make_tab()
hairdresser_frame       = _make_tab()
clients_frame           = _make_tab()
products_frame          = _make_tab()
hairdresser_bookings_frame = _make_tab()
orders_frame            = _make_tab()
financials_frame        = _make_tab()

ALL_FRAMES = [dashboard_frame, hairdresser_frame, clients_frame,
              products_frame, hairdresser_bookings_frame, orders_frame, financials_frame]

for f in ALL_FRAMES:
    f.grid(row=0, column=0, sticky="nsew")

# ═══════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════

_dash_kpi_vals = {}

def draw_7day(parent):
    clear_frame(parent)
    labels, svc, prod = db_7day_revenue()
    fig, ax = _chart_fig(6.5, 3.2)
    x = range(len(labels))
    ax.plot(x, svc,  color=C_GOLD,    marker="o", lw=2, ms=5, label="Services")
    ax.plot(x, prod, color=C_SUCCESS,  marker="s", lw=2, ms=5, label="Products")
    ax.fill_between(x, svc,  alpha=0.12, color=C_GOLD)
    ax.fill_between(x, prod, alpha=0.12, color=C_SUCCESS)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, color=C_MUTED, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:.0f}"))
    ax.tick_params(axis="y", colors=C_MUTED)
    ax.set_title("7-Day Revenue", color=C_TEXT, fontsize=12, pad=8)
    leg = ax.legend(facecolor=C_SURFACE2, labelcolor=C_TEXT, fontsize=9, framealpha=0.9)
    plt.tight_layout(pad=1.2)
    embed_chart(fig, parent)

def draw_monthly_svcs(parent):
    clear_frame(parent)
    data = db_monthly_services()
    if not data:
        CTkLabel(parent, text="No bookings this month", text_color=C_MUTED, font=FONT_BODY).pack(expand=True)
        return
    names  = [r[0] for r in data][:6]
    counts = [r[1] for r in data][:6]
    cols   = [C_GOLD if i==0 else C_GOLD_DARK if i==1 else C_MUTED for i in range(len(names))]
    fig, ax = _chart_fig(5, 3.2)
    bars = ax.barh(names[::-1], counts[::-1], color=cols[::-1], height=0.5)
    for bar in bars:
        w = bar.get_width()
        ax.text(w+0.1, bar.get_y()+bar.get_height()/2, str(int(w)), va="center", color=C_MUTED, fontsize=9)
    ax.set_title("Services This Month", color=C_TEXT, fontsize=12, pad=8)
    ax.tick_params(axis="y", colors=C_MUTED, labelsize=9)
    ax.tick_params(axis="x", colors=C_MUTED)
    plt.tight_layout(pad=1.2)
    embed_chart(fig, parent)

def draw_status_donut(parent):
    clear_frame(parent)
    upcoming, completed, canceled = db_booking_statuses()
    total = upcoming + completed + canceled
    if not total:
        CTkLabel(parent, text="No bookings\nthis month", text_color=C_MUTED, font=FONT_BODY).pack(expand=True)
        return
    sizes  = [upcoming, completed, canceled]
    labels = [f"Upcoming ({upcoming})", f"Completed ({completed})", f"Canceled ({canceled})"]
    colors = [C_WARNING, C_SUCCESS, C_DANGER]
    valid = [(s,l,c) for s,l,c in zip(sizes,labels,colors) if s>0]
    if not valid: return
    s,l,c = zip(*valid)
    fig, ax = _chart_fig(3.8, 3.2)
    ax.pie(s, labels=l, colors=c, autopct="%1.0f%%", startangle=90,
           pctdistance=0.75, wedgeprops=dict(width=0.52),
           textprops={"color": C_MUTED, "fontsize": 8})
    ax.set_title("Booking Status", color=C_TEXT, fontsize=12, pad=8)
    plt.tight_layout(pad=1.0)
    embed_chart(fig, parent)

def _booking_filter_bar(parent, on_upcoming, on_all, on_canceled):
    bar = CTkFrame(parent, fg_color="transparent")
    bar.pack(fill="x", padx=PAD, pady=(8, 4))
    btns = {}
    def activate(key):
        for k,b in btns.items():
            b.configure(fg_color=C_GOLD if k==key else "transparent",
                        text_color="#1a1a1a" if k==key else C_TEXT_DIM)
    b1 = _ghost_btn(bar, "Upcoming", lambda:[activate("u"), on_upcoming()], width=120)
    b2 = _ghost_btn(bar, "All",      lambda:[activate("a"), on_all()],      width=90)
    b3 = _ghost_btn(bar, "Canceled", lambda:[activate("c"), on_canceled()], width=110)
    b1.configure(fg_color=C_GOLD, text_color="#1a1a1a")
    for b in [b1,b2,b3]: b.pack(side="left", padx=(0,6))
    btns.update({"u":b1,"a":b2,"c":b3})

_dash_booking_table = None

def _render_bookings(bookings):
    if not (_dash_booking_table and _dash_booking_table.winfo_exists()): return
    clear_frame(_dash_booking_table)
    headers = ["Client","Service","Date","Slot","Hairdresser","Status",""]
    render_table_headers(_dash_booking_table, headers)
    if not bookings:
        empty_state(_dash_booking_table, "No bookings found", 7); return
    for i, b in enumerate(bookings):
        bid, client, svc, dv, sv, hair, status = b
        table_cell(_dash_booking_table, client,                       i, 0)
        table_cell(_dash_booking_table, svc,                          i, 1)
        table_cell(_dash_booking_table, format_date(dv, "%d/%m/%Y"),  i, 2)
        table_cell(_dash_booking_table, format_slot(sv),              i, 3)
        table_cell(_dash_booking_table, hair,                         i, 4)
        status_badge(_dash_booking_table, status,                     i, 5)
        _ghost_btn(_dash_booking_table, "Edit", lambda bid=bid: edit_booking_popup(bid), width=60, height=28
                   ).grid(row=i+2, column=6, padx=8, pady=5)

def create_dashboard():
    global _dash_booking_table, _dash_kpi_vals
    clear_frame(dashboard_frame)

    scroll = CTkScrollableFrame(dashboard_frame, fg_color=C_BG, scrollbar_button_color=C_BORDER)
    scroll.pack(fill="both", expand=True)

    # ── KPI row 1 ──
    k1 = CTkFrame(scroll, fg_color="transparent")
    k1.pack(fill="x", padx=PAD, pady=(PAD, 0))
    for c in range(3): k1.grid_columnconfigure(c, weight=1)
    _, v1 = kpi_card(k1, "Total Clients",    "--", "all time",           C_GOLD,    0, 0)
    _, v2 = kpi_card(k1, "Bookings Today",   "--", "non-canceled",       C_WARNING, 0, 1)
    _, v3 = kpi_card(k1, "Revenue Today",    "--", "completed services",  C_SUCCESS, 0, 2)

    # ── KPI row 2 ──
    k2 = CTkFrame(scroll, fg_color="transparent")
    k2.pack(fill="x", padx=PAD, pady=(0, 4))
    for c in range(3): k2.grid_columnconfigure(c, weight=1)
    _, v4 = kpi_card(k2, "Monthly Revenue",   "--", "services + products", "#9b7fe8", 0, 0)
    _, v5 = kpi_card(k2, "Cancellation Rate", "--", "this month",          C_DANGER,  0, 1)
    _, v6 = kpi_card(k2, "Avg Service Value", "--", "all completed",       C_SUCCESS,  0, 2)

    _dash_kpi_vals = {"v1":v1,"v2":v2,"v3":v3,"v4":v4,"v5":v5,"v6":v6}

    # ── Quick stats band ──
    band = CTkFrame(scroll, fg_color=C_SURFACE, corner_radius=RADIUS)
    band.pack(fill="x", padx=PAD, pady=(4, 8))
    for c in range(4): band.grid_columnconfigure(c, weight=1)
    quick_stats = [
        ("📅  Busiest Day",        db_busiest_day()),
        ("✂️  Top Hairdresser",    db_top_hairdresser()),
        ("⭐  Top Service",         db_top_service()),
        ("📦  Low Stock Items",     str(len(db_low_stock()))),
    ]
    for c, (label, val) in enumerate(quick_stats):
        cell = CTkFrame(band, fg_color="transparent")
        cell.grid(row=0, column=c, padx=PAD, pady=PAD, sticky="w")
        CTkLabel(cell, text=label, font=FONT_SMALL, text_color=C_MUTED).pack(anchor="w")
        CTkLabel(cell, text=val,   font=FONT_BOLD,  text_color=C_TEXT).pack(anchor="w", pady=(2,0))

    # ── Low stock alert (conditional) ──
    low = db_low_stock()
    if low:
        alert = CTkFrame(scroll, fg_color=C_SURFACE2, corner_radius=RADIUS,
                         border_width=1, border_color=C_WARNING)
        alert.pack(fill="x", padx=PAD, pady=(0, 8))
        hrow = CTkFrame(alert, fg_color="transparent")
        hrow.pack(fill="x", padx=PAD, pady=(10, 4))
        CTkLabel(hrow, text="⚠  Low Stock Alert", font=FONT_BOLD, text_color=C_WARNING).pack(side="left")
        CTkLabel(hrow, text=f"{len(low)} item(s) need restocking", font=FONT_SMALL, text_color=C_MUTED).pack(side="left", padx=10)
        tagrow = CTkFrame(alert, fg_color="transparent")
        tagrow.pack(fill="x", padx=PAD, pady=(0, 10))
        for name, stock in low:
            col = C_DANGER if stock == 0 else C_WARNING
            tag = CTkFrame(tagrow, fg_color=col, corner_radius=8)
            tag.pack(side="left", padx=(0, 8))
            CTkLabel(tag, text=f"  {'OUT' if stock==0 else stock}  {name}  ",
                     font=FONT_SMALL, text_color="white").pack(padx=2, pady=3)

    # ── Charts ──
    charts = CTkFrame(scroll, fg_color="transparent")
    charts.pack(fill="x", padx=PAD, pady=(0, 8))
    charts.grid_columnconfigure(0, weight=5)
    charts.grid_columnconfigure(1, weight=4)
    charts.grid_columnconfigure(2, weight=3)

    c1 = CTkFrame(charts, fg_color=C_SURFACE, corner_radius=RADIUS)
    c1.grid(row=0, column=0, padx=(0,6), pady=0, sticky="nsew")
    c2 = CTkFrame(charts, fg_color=C_SURFACE, corner_radius=RADIUS)
    c2.grid(row=0, column=1, padx=6, pady=0, sticky="nsew")
    c3 = CTkFrame(charts, fg_color=C_SURFACE, corner_radius=RADIUS)
    c3.grid(row=0, column=2, padx=(6,0), pady=0, sticky="nsew")

    cf1 = CTkFrame(c1, fg_color="transparent")
    cf1.pack(fill="both", expand=True, padx=8, pady=8)
    cf2 = CTkFrame(c2, fg_color="transparent")
    cf2.pack(fill="both", expand=True, padx=8, pady=8)
    cf3 = CTkFrame(c3, fg_color="transparent")
    cf3.pack(fill="both", expand=True, padx=8, pady=8)

    # ── Bookings table ──
    btable_card = CTkFrame(scroll, fg_color=C_SURFACE, corner_radius=RADIUS)
    btable_card.pack(fill="x", padx=PAD, pady=(0, PAD))

    bheader = CTkFrame(btable_card, fg_color="transparent")
    bheader.pack(fill="x", padx=PAD, pady=(PAD, 0))

    CTkLabel(bheader, text="Bookings", font=FONT_SECTION, text_color=C_TEXT).pack(side="left")

    _gold_btn(bheader, "+ Add Booking", add_booking_popup, width=140).pack(side="right")

    _dash_booking_table = CTkScrollableFrame(btable_card, fg_color="transparent", height=240,
                                              scrollbar_button_color=C_BORDER)
    _dash_booking_table.pack(fill="x", padx=PAD, pady=(4, PAD))

    _booking_filter_bar(btable_card,
        on_upcoming=lambda: _render_bookings(db_upcoming_bookings()),
        on_all=lambda:      _render_bookings(db_all_bookings()),
        on_canceled=lambda: _render_bookings(db_canceled_bookings())
    )

    # populate everything after layout renders
    def _populate():
        v1.configure(text=str(db_total_clients()))
        v2.configure(text=str(db_bookings_today()))
        v3.configure(text=f"${db_revenue_today():.2f}")
        v4.configure(text=f"${db_monthly_revenue():.2f}")
        v5.configure(text=f"{db_cancel_rate()}%")
        v6.configure(text=f"${db_avg_service():.2f}")
        draw_7day(cf1)
        draw_monthly_svcs(cf2)
        draw_status_donut(cf3)
        _render_bookings(db_upcoming_bookings())

    app.after(80, _populate)

def refresh_dashboard():
    if _active_tab[0] == "Dashboard":
        create_dashboard()

# ═══════════════════════════════════════════════════════════════
#  BOOKING POPUPS
# ═══════════════════════════════════════════════════════════════

def _booking_form(panel, client_map, hair_map, svc_map, slot_map):
    CTkLabel(panel, text="Client",      font=FONT_SMALL, text_color=C_TEXT_DIM).grid(row=1,column=0,sticky="w",padx=PAD,pady=(10,3))
    cb_c = CTkComboBox(panel, values=list(client_map.keys()), width=230,
                       fg_color=C_SURFACE2, border_color=C_BORDER, text_color=C_TEXT,
                       button_color=C_GOLD, dropdown_fg_color=C_SURFACE2)
    cb_c.grid(row=2,column=0,padx=PAD,pady=(0,PAD))

    CTkLabel(panel, text="Service",     font=FONT_SMALL, text_color=C_TEXT_DIM).grid(row=1,column=1,sticky="w",padx=PAD,pady=(10,3))
    cb_s = CTkComboBox(panel, values=list(svc_map.keys()),    width=230,
                       fg_color=C_SURFACE2, border_color=C_BORDER, text_color=C_TEXT,
                       button_color=C_GOLD, dropdown_fg_color=C_SURFACE2)
    cb_s.grid(row=2,column=1,padx=PAD,pady=(0,PAD))

    CTkLabel(panel, text="Hairdresser", font=FONT_SMALL, text_color=C_TEXT_DIM).grid(row=3,column=0,sticky="w",padx=PAD,pady=(10,3))
    cb_h = CTkComboBox(panel, values=list(hair_map.keys()),   width=230,
                       fg_color=C_SURFACE2, border_color=C_BORDER, text_color=C_TEXT,
                       button_color=C_GOLD, dropdown_fg_color=C_SURFACE2)
    cb_h.grid(row=4,column=0,padx=PAD,pady=(0,PAD))

    date_e = labeled_entry(panel, "Date (YYYY-MM-DD)", 3, 1, placeholder="YYYY-MM-DD")

    CTkLabel(panel, text="Slot",        font=FONT_SMALL, text_color=C_TEXT_DIM).grid(row=5,column=0,sticky="w",padx=PAD,pady=(10,3))
    cb_sl = CTkComboBox(panel, values=list(slot_map.keys()),  width=230,
                        fg_color=C_SURFACE2, border_color=C_BORDER, text_color=C_TEXT,
                        button_color=C_GOLD, dropdown_fg_color=C_SURFACE2)
    cb_sl.grid(row=6,column=0,padx=PAD,pady=(0,PAD))

    sw = CTkSwitch(panel, text="Mark Completed", progress_color=C_GOLD, button_color=C_GOLD_DARK)
    sw.grid(row=6,column=1,padx=PAD,pady=(0,PAD),sticky="w")
    return cb_c, cb_s, cb_h, date_e, cb_sl, sw

def edit_booking_popup(booking_id):
    overlay, panel, err = overlay_modal(app, "Edit Booking")
    cm, hm, sm, slm, slr = db_booking_refs()
    cursor.execute("SELECT ClientID,HairdresserID,ServiceID,[Date],Slot,IsCompleted FROM Bookings WHERE BookingID=?", (booking_id,))
    bk = cursor.fetchone()
    if not bk: err.configure(text="Booking not found."); return
    cc,hc,sc,dc,slc,compc = bk
    cb_c,cb_s,cb_h,de,cb_sl,sw = _booking_form(panel,cm,hm,sm,slm)
    cb_c.set(next(k for k,v in cm.items() if v==cc))
    cb_s.set(next(k for k,v in sm.items() if v==sc))
    cb_h.set(next(k for k,v in hm.items() if v==hc))
    de.insert(0, format_date(dc))
    cb_sl.set(slr[slc])
    if compc: sw.select()
    def save():
        try:
            cid = cm[cb_c.get()]
            sid = sm[cb_s.get()]
            hid = hm[cb_h.get()]
            slid = slm[cb_sl.get()]
            dv = de.get().strip()

            cursor.execute(
                "SELECT COUNT(*) FROM Bookings WHERE HairdresserID=? AND Slot=? AND [Date]=? AND BookingID<>? AND Canceled=False",
                (hid, slid, dv, booking_id)
            )
            if cursor.fetchone()[0] > 0:
                err.configure(text="Hairdresser already booked for that slot.")
                return

            old_completed = 1 if compc else 0
            new_completed = sw.get()

            cursor.execute(
                "UPDATE Bookings SET ClientID=?,HairdresserID=?,ServiceID=?,[Date]=?,Slot=?,IsCompleted=? WHERE BookingID=?",
                (cid, hid, sid, dv, slid, new_completed, booking_id)
            )
            conn.commit()

            if old_completed == 0 and new_completed == 1:
                add_commission_expense(booking_id)

            overlay.destroy()
            refresh_dashboard()

        except Exception as e:
            err.configure(text="Please fill all fields correctly.")

    def cancel_bk():
        cursor.execute("UPDATE Bookings SET Canceled=True WHERE BookingID=?",(booking_id,))
        conn.commit(); overlay.destroy(); refresh_dashboard()
    modal_buttons(panel,overlay,save,cancel_bk,"Save Changes","Cancel Booking")

def add_booking_popup():
    overlay, panel, err = overlay_modal(app, "Add Booking")
    cm, hm, sm, slm, _ = db_booking_refs()
    cb_c,cb_s,cb_h,de,cb_sl,sw = _booking_form(panel,cm,hm,sm,slm)
    if cm:  cb_c.set(list(cm.keys())[0])
    if sm:  cb_s.set(list(sm.keys())[0])
    if hm:  cb_h.set(list(hm.keys())[0])
    if slm: cb_sl.set(list(slm.keys())[0])
    def save():
        try:
            cid=cm[cb_c.get()]; sid=sm[cb_s.get()]; hid=hm[cb_h.get()]
            slid=slm[cb_sl.get()]; dv=de.get().strip()
            if not dv: err.configure(text="Please enter a date."); return
            cursor.execute("SELECT COUNT(*) FROM Bookings WHERE HairdresserID=? AND Slot=? AND [Date]=? AND Canceled=False",(hid,slid,dv))
            if cursor.fetchone()[0]>0: err.configure(text="Hairdresser already booked for that slot."); return
            cursor.execute("INSERT INTO Bookings(ClientID,HairdresserID,ServiceID,[Date],Slot,IsCompleted,Canceled) VALUES(?,?,?,?,?,?,False)",(cid,hid,sid,dv,slid,sw.get()))
            conn.commit(); overlay.destroy(); refresh_dashboard()
        except: err.configure(text="Please fill all fields correctly.")
    modal_buttons(panel,overlay,save,save_text="Add Booking")

# ═══════════════════════════════════════════════════════════════
#  HAIRDRESSERS
# ═══════════════════════════════════════════════════════════════

def db_hairdressers(search=""):
    if search.strip():
        s = f"%{search.strip()}%"
        cursor.execute("SELECT HairdresserID,HairdresserName,YearsOfExperience,[Additional Notes],ProfilePicture FROM Hairdressers WHERE HairdresserName LIKE ? OR [Additional Notes] LIKE ? ORDER BY HairdresserName",(s,s))
    else:
        cursor.execute("SELECT HairdresserID,HairdresserName,YearsOfExperience,[Additional Notes],ProfilePicture FROM Hairdressers ORDER BY HairdresserName")
    return cursor.fetchall()

def refresh_hairdresser_page():
    clear_frame(hairdresser_frame)
    _build_hairdressers(hairdresser_frame)

def _build_hairdressers(parent):
    global hairdresser_search_var
    if hairdresser_search_var is None:
        hairdresser_search_var = StringVar(value="")

    top = CTkFrame(parent, fg_color="transparent")
    top.pack(fill="x", padx=PAD, pady=(PAD, 8))
    CTkLabel(top, text="Hairdressers", font=FONT_TITLE, text_color=C_TEXT).pack(side="left")
    ctrl = CTkFrame(top, fg_color="transparent")
    ctrl.pack(side="right")

    se = CTkEntry(ctrl, width=200, textvariable=hairdresser_search_var,
                  fg_color=C_SURFACE, border_color=C_BORDER, text_color=C_TEXT,
                  placeholder_text="Search…", placeholder_text_color=C_MUTED)
    se.pack(side="left", padx=(0,6))
    se.bind("<Return>", lambda e: refresh_hairdresser_page())
    _ghost_btn(ctrl,"Search", refresh_hairdresser_page, width=80).pack(side="left", padx=(0,4))
    _ghost_btn(ctrl,"Clear",  lambda:[hairdresser_search_var.set(""), refresh_hairdresser_page()], width=70).pack(side="left", padx=(0,10))

    view_var = StringVar(value=hairdresser_view_mode)
    def _set_view(v):
        global hairdresser_view_mode
        hairdresser_view_mode = v
        refresh_hairdresser_page()

    seg = CTkSegmentedButton(ctrl, values=["Cards","Table"], variable=view_var,
                             command=lambda v: _set_view(v.lower()),
                             selected_color=C_GOLD, selected_hover_color=C_GOLD_DARK,
                             unselected_color=C_SURFACE, fg_color=C_SURFACE2,
                             text_color=C_TEXT, font=FONT_BODY)
    seg.pack(side="left", padx=(0,10))
    seg.set("Cards" if hairdresser_view_mode=="cards" else "Table")

    _gold_btn(ctrl,"+ Add Hairdresser", add_hairdresser_popup, width=150).pack(side="left")

    body = CTkFrame(parent, fg_color="transparent")
    body.pack(fill="both", expand=True)
    data = db_hairdressers(hairdresser_search_var.get())

    if hairdresser_view_mode == "cards":
        _hairdresser_cards(body, data)
    else:
        _hairdresser_table(body, data)

def _hairdresser_cards(parent, data):
    scroll = CTkScrollableFrame(parent, fg_color="transparent", scrollbar_button_color=C_BORDER)
    scroll.pack(fill="both", expand=True, padx=PAD)
    cols = 4
    for c in range(cols): scroll.grid_columnconfigure(c, weight=1, uniform="h")

    for idx, h in enumerate(data):
        hid,name,exp,notes,img = h
        r,c = divmod(idx, cols)
        card = CTkFrame(scroll, fg_color=C_SURFACE, corner_radius=RADIUS)
        card.grid(row=r, column=c, padx=10, pady=10, sticky="ew")
        av = build_avatar(img, (90,90), circle=True)
        il = CTkLabel(card, image=av, text=""); il.image=av; il.pack(pady=(18,8))
        CTkLabel(card, text=name,  font=FONT_BOLD, text_color=C_TEXT).pack()
        CTkLabel(card, text=f"{exp} yrs exp" if exp else "—", font=FONT_SMALL, text_color=C_MUTED).pack(pady=2)
        CTkLabel(card, text=notes if notes else "No notes", font=FONT_SMALL, text_color=C_MUTED, wraplength=180).pack(pady=(2,12))
        CTkFrame(card, fg_color=C_BORDER, height=1).pack(fill="x", padx=16)
        _ghost_btn(card,"Edit", lambda id=hid: edit_hairdresser_popup(id), width=80, height=30).pack(pady=12)

    # add card
    ai = len(data); ar,ac = divmod(ai,cols)
    add = CTkFrame(scroll, fg_color=C_SURFACE, corner_radius=RADIUS)
    add.grid(row=ar,column=ac,padx=10,pady=10,sticky="ew")
    plus = build_plus_icon((60,60))
    CTkLabel(add, text="Add", font=FONT_BOLD, text_color=C_GOLD).pack(pady=(24,8))
    ab = CTkButton(add, text="", image=plus, fg_color="transparent", hover_color=C_SURFACE2,
                   width=80, height=80, command=add_hairdresser_popup)
    ab.pack(); ab.image=plus
    CTkLabel(add, text="New employee", font=FONT_SMALL, text_color=C_MUTED).pack(pady=(4,24))

def _hairdresser_table(parent, data):
    wrap = CTkScrollableFrame(parent, fg_color="transparent", scrollbar_button_color=C_BORDER)
    wrap.pack(fill="both", expand=True, padx=PAD, pady=8)
    headers = ["Name","Experience","Notes",""]
    render_table_headers(wrap, headers, [2,1,3,1])
    if not data: empty_state(wrap,"No hairdressers found.",4); return
    for i,h in enumerate(data):
        hid,name,exp,notes,_ = h
        table_cell(wrap,name,i,0,bold=True)
        table_cell(wrap,f"{exp} yrs" if exp else "—",i,1)
        table_cell(wrap,notes if notes else "—",i,2,wraplength=280)
        _ghost_btn(wrap,"Edit",lambda id=hid: edit_hairdresser_popup(id),width=70,height=30
                   ).grid(row=i+2,column=3,padx=8,pady=5)

def _hairdresser_form(panel):
    ne = labeled_entry(panel,"Hairdresser Name",1,0)
    ee = labeled_entry(panel,"Years of Experience",1,1)
    no = labeled_entry(panel,"Additional Notes",3,0)
    pe = labeled_entry(panel,"Profile Picture Path",3,1)
    return ne,ee,no,pe

def edit_hairdresser_popup(hid):
    overlay,panel,err = overlay_modal(app,"Edit Hairdresser")
    cursor.execute("SELECT HairdresserName,YearsOfExperience,[Additional Notes],ProfilePicture FROM Hairdressers WHERE HairdresserID=?",(hid,))
    h = cursor.fetchone()
    if not h: err.configure(text="Not found."); return
    ne,ee,no,pe = _hairdresser_form(panel)
    ne.insert(0,h[0] or ""); ee.insert(0,str(h[1] or "")); no.insert(0,h[2] or ""); pe.insert(0,h[3] or "")
    def save():
        n=ne.get().strip()
        if not n: err.configure(text="Name required."); return
        try: exp=int(ee.get().strip())
        except: err.configure(text="Experience must be a number."); return
        cursor.execute("UPDATE Hairdressers SET HairdresserName=?,YearsOfExperience=?,[Additional Notes]=?,ProfilePicture=? WHERE HairdresserID=?",(n,exp,no.get().strip(),pe.get().strip(),hid))
        conn.commit(); overlay.destroy(); refresh_hairdresser_page()
    def delete():
        try: cursor.execute("DELETE FROM Hairdressers WHERE HairdresserID=?",(hid,)); conn.commit()
        except Exception as e: err.configure(text=str(e)); return
        overlay.destroy(); refresh_hairdresser_page()
    modal_buttons(panel,overlay,save,delete,"Save Changes","Delete")

def add_hairdresser_popup():
    overlay,panel,err = overlay_modal(app,"Add Hairdresser")
    ne,ee,no,pe = _hairdresser_form(panel)
    def save():
        n=ne.get().strip()
        if not n: err.configure(text="Name required."); return
        try: exp=int(ee.get().strip())
        except: err.configure(text="Experience must be a number."); return
        cursor.execute("INSERT INTO Hairdressers(HairdresserName,YearsOfExperience,[Additional Notes],ProfilePicture) VALUES(?,?,?,?)",(n,exp,no.get().strip(),pe.get().strip()))
        conn.commit(); overlay.destroy(); refresh_hairdresser_page()
    modal_buttons(panel,overlay,save,save_text="Create")

# ═══════════════════════════════════════════════════════════════
#  CLIENTS
# ═══════════════════════════════════════════════════════════════

def db_clients(search=""):
    if search.strip():
        s=f"%{search.strip()}%"
        cursor.execute("SELECT ClientID,ClientName,Email,PhoneNumber,ProfilePicture FROM Clients WHERE ClientName LIKE ? OR PhoneNumber LIKE ? ORDER BY ClientName",(s,s))
    else:
        cursor.execute("SELECT ClientID,ClientName,Email,PhoneNumber,ProfilePicture FROM Clients ORDER BY ClientName")
    return cursor.fetchall()

def refresh_clients_page():
    clear_frame(clients_frame)
    _build_clients(clients_frame)

def _build_clients(parent):
    global client_search_var, client_view_mode
    if client_search_var is None: client_search_var = StringVar(value="")

    top = CTkFrame(parent, fg_color="transparent")
    top.pack(fill="x", padx=PAD, pady=(PAD,8))
    CTkLabel(top, text="Clients", font=FONT_TITLE, text_color=C_TEXT).pack(side="left")
    ctrl = CTkFrame(top, fg_color="transparent"); ctrl.pack(side="right")

    se = CTkEntry(ctrl, width=200, textvariable=client_search_var,
                  fg_color=C_SURFACE, border_color=C_BORDER, text_color=C_TEXT,
                  placeholder_text="Search name or phone…", placeholder_text_color=C_MUTED)
    se.pack(side="left", padx=(0,6))
    se.bind("<Return>", lambda e: refresh_clients_page())
    _ghost_btn(ctrl,"Search",refresh_clients_page,width=80).pack(side="left",padx=(0,4))
    _ghost_btn(ctrl,"Clear",lambda:[client_search_var.set(""),refresh_clients_page()],width=70).pack(side="left",padx=(0,10))

    view_var = StringVar(value=client_view_mode)
    seg = CTkSegmentedButton(ctrl, values=["Cards","Table"], variable=view_var,
                             command=lambda v: _set_client_view(v.lower()),
                             selected_color=C_GOLD, selected_hover_color=C_GOLD_DARK,
                             unselected_color=C_SURFACE, fg_color=C_SURFACE2,
                             text_color=C_TEXT, font=FONT_BODY)
    seg.pack(side="left", padx=(0,10))
    seg.set("Cards" if client_view_mode=="cards" else "Table")
    _gold_btn(ctrl,"+ Add Client",add_client_popup,width=130).pack(side="left")

    body = CTkFrame(parent, fg_color="transparent"); body.pack(fill="both", expand=True)
    data = db_clients(client_search_var.get())
    if client_view_mode=="cards": _client_cards(body, data)
    else: _client_table(body, data)

def _set_client_view(v):
    global client_view_mode
    client_view_mode = v
    refresh_clients_page()

def _client_cards(parent, data):
    scroll = CTkScrollableFrame(parent, fg_color="transparent", scrollbar_button_color=C_BORDER)
    scroll.pack(fill="both", expand=True, padx=PAD)
    cols = 4
    for c in range(cols): scroll.grid_columnconfigure(c,weight=1,uniform="cl")
    for idx, cl in enumerate(data):
        cid,name,email,phone,img = cl
        r,c = divmod(idx,cols)
        card = CTkFrame(scroll, fg_color=C_SURFACE, corner_radius=RADIUS)
        card.grid(row=r,column=c,padx=10,pady=10,sticky="ew")
        av = build_avatar(img,(90,90),circle=True)
        il = CTkLabel(card,image=av,text=""); il.image=av; il.pack(pady=(18,8))
        CTkLabel(card,text=name,font=FONT_BOLD,text_color=C_TEXT).pack()
        CTkLabel(card,text=email or "No email",font=FONT_SMALL,text_color=C_MUTED,wraplength=180).pack(pady=2)
        CTkLabel(card,text=phone or "No phone",font=FONT_SMALL,text_color=C_MUTED).pack(pady=(2,12))
        CTkFrame(card,fg_color=C_BORDER,height=1).pack(fill="x",padx=16)
        br = CTkFrame(card,fg_color="transparent"); br.pack(pady=12)
        _ghost_btn(br,"Edit",lambda id=cid: edit_client_popup(id),width=72,height=30).pack(side="left",padx=3)
        _gold_btn(br,"Overview",lambda id=cid: client_overview_popup(id),width=90,height=30).pack(side="left",padx=3)
    ai=len(data); ar,ac=divmod(ai,cols)
    add=CTkFrame(scroll,fg_color=C_SURFACE,corner_radius=RADIUS)
    add.grid(row=ar,column=ac,padx=10,pady=10,sticky="ew")
    plus=build_plus_icon((60,60))
    CTkLabel(add,text="Add Client",font=FONT_BOLD,text_color=C_GOLD).pack(pady=(24,8))
    ab=CTkButton(add,text="",image=plus,fg_color="transparent",hover_color=C_SURFACE2,width=80,height=80,command=add_client_popup)
    ab.pack(); ab.image=plus
    CTkLabel(add,text="New client profile",font=FONT_SMALL,text_color=C_MUTED).pack(pady=(4,24))

def _client_table(parent,data):
    wrap=CTkScrollableFrame(parent,fg_color="transparent",scrollbar_button_color=C_BORDER)
    wrap.pack(fill="both",expand=True,padx=PAD,pady=8)
    headers=["Name","Email","Phone",""]
    render_table_headers(wrap,headers,[2,2,2,1])
    if not data: empty_state(wrap,"No clients found.",4); return
    for i,cl in enumerate(data):
        cid,name,email,phone,_ = cl
        table_cell(wrap,name,i,0,bold=True)
        table_cell(wrap,email or "—",i,1)
        table_cell(wrap,phone or "—",i,2)
        bf=CTkFrame(wrap,fg_color="transparent")
        bf.grid(row=i+2,column=3,padx=8,pady=5,sticky="w")
        _ghost_btn(bf,"Edit",lambda id=cid: edit_client_popup(id),width=65,height=28).pack(side="left",padx=2)
        _gold_btn(bf,"Overview",lambda id=cid: client_overview_popup(id),width=85,height=28).pack(side="left",padx=2)

def client_overview_popup(client_id):
    overlay = CTkFrame(app, fg_color="#000000")
    overlay.place(relx=0,rely=0,relwidth=1,relheight=1); overlay.lift()
    panel = CTkFrame(overlay, fg_color=C_SURFACE, corner_radius=18)
    panel.place(relx=0.5,rely=0.5,anchor="center",relwidth=0.94,relheight=0.92)
    panel.grid_rowconfigure(2,weight=1); panel.grid_rowconfigure(3,weight=1)
    panel.grid_columnconfigure(0,weight=1)

    cursor.execute("SELECT ClientName,Email,PhoneNumber,DateJoined,ProfilePicture FROM Clients WHERE ClientID=?",(client_id,))
    cl=cursor.fetchone()
    if not cl: CTkLabel(panel,text="Client not found.",text_color=C_DANGER).pack(pady=20); return
    name,email,phone,joined,pic=cl

    cursor.execute("SELECT COUNT(*) FROM Bookings WHERE ClientID=? AND IsCompleted=True AND Canceled=False",(client_id,))
    visits=safe_int(cursor.fetchone()[0])
    cursor.execute("SELECT SUM(Services.Price) FROM Bookings INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID WHERE Bookings.ClientID=? AND Bookings.IsCompleted=True AND Bookings.Canceled=False",(client_id,))
    svc_spent=safe_float(cursor.fetchone()[0])
    cursor.execute("SELECT AVG(Services.Price) FROM Bookings INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID WHERE Bookings.ClientID=? AND Bookings.IsCompleted=True AND Bookings.Canceled=False",(client_id,))
    avg_spend=safe_float(cursor.fetchone()[0])
    cursor.execute("SELECT TOP 1 Services.ServiceName FROM Bookings INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID WHERE Bookings.ClientID=? AND Bookings.IsCompleted=True AND Bookings.Canceled=False GROUP BY Services.ServiceName ORDER BY COUNT(*) DESC",(client_id,))
    fav_r=cursor.fetchone(); fav_svc=fav_r[0] if fav_r else "—"
    cursor.execute("SELECT SUM(OrderItems.Quantity*OrderItems.PriceAtSale),SUM(OrderItems.Quantity) FROM Orders INNER JOIN OrderItems ON Orders.OrderID=OrderItems.OrderID WHERE Orders.ClientID=?",(client_id,))
    pr=cursor.fetchone(); prod_spent=safe_float(pr[0]); prod_items=safe_int(pr[1])
    cursor.execute("SELECT TOP 1 Products.ProductName FROM (Orders INNER JOIN OrderItems ON Orders.OrderID=OrderItems.OrderID) INNER JOIN Products ON OrderItems.ProductID=Products.ProductID WHERE Orders.ClientID=? GROUP BY Products.ProductName ORDER BY SUM(OrderItems.Quantity) DESC",(client_id,))
    fp_r=cursor.fetchone(); fav_prod=fp_r[0] if fp_r else "—"

    # header
    hdr=CTkFrame(panel,fg_color=C_SURFACE2,corner_radius=0,height=70)
    hdr.grid(row=0,column=0,sticky="ew"); hdr.grid_propagate(False)
    hdr.grid_columnconfigure(0,weight=1)
    av=build_avatar(pic,(52,52),circle=True)
    il=CTkLabel(hdr,image=av,text=""); il.image=av; il.grid(row=0,column=0,sticky="w",padx=PAD,pady=10)
    info=CTkFrame(hdr,fg_color="transparent"); info.grid(row=0,column=0,sticky="w",padx=(80,0))
    CTkLabel(info,text=name,font=FONT_SECTION,text_color=C_TEXT).pack(anchor="w")
    CTkLabel(info,text=f"{email or '—'}  •  {phone or '—'}  •  Joined {format_date(joined)}",font=FONT_SMALL,text_color=C_MUTED).pack(anchor="w")
    CTkButton(hdr,text="✕",width=36,height=36,fg_color="transparent",hover_color=C_DANGER,text_color=C_TEXT_DIM,command=overlay.destroy).grid(row=0,column=1,padx=PAD)

    # stats
    sb=CTkFrame(panel,fg_color="transparent"); sb.grid(row=1,column=0,sticky="ew",padx=PAD,pady=8)
    for c in range(4): sb.grid_columnconfigure(c,weight=1)
    def _mini_kpi(p,title,val,r,c,acc=C_GOLD):
        card=CTkFrame(p,fg_color=C_SURFACE2,corner_radius=10); card.grid(row=r,column=c,padx=6,pady=6,sticky="nsew")
        CTkFrame(card,fg_color=acc,height=3,corner_radius=2).pack(fill="x")
        CTkLabel(card,text=title,font=FONT_SMALL,text_color=C_MUTED).pack(anchor="w",padx=10,pady=(6,2))
        CTkLabel(card,text=val,font=("Inter",15,"bold"),text_color=C_TEXT).pack(anchor="w",padx=10,pady=(0,8))
    _mini_kpi(sb,"Visits",str(visits),0,0)
    _mini_kpi(sb,"Fav Service",fav_svc,0,1)
    _mini_kpi(sb,"Service Spend",f"${svc_spent:.2f}",0,2,C_SUCCESS)
    _mini_kpi(sb,"Avg Spend",f"${avg_spend:.2f}",0,3,C_WARNING)
    _mini_kpi(sb,"Product Spend",f"${prod_spent:.2f}",1,0,C_SUCCESS)
    _mini_kpi(sb,"Items Bought",str(prod_items),1,1)
    _mini_kpi(sb,"Fav Product",fav_prod,1,2)
    _mini_kpi(sb,"Lifetime Value",f"${svc_spent+prod_spent:.2f}",1,3,C_GOLD)

    # visit history
    vp=CTkFrame(panel,fg_color=C_SURFACE2,corner_radius=RADIUS); vp.grid(row=2,column=0,sticky="nsew",padx=PAD,pady=(0,6))
    vp.grid_rowconfigure(1,weight=1); vp.grid_columnconfigure(0,weight=1)
    vh=CTkFrame(vp,fg_color="transparent"); vh.grid(row=0,column=0,sticky="ew",padx=PAD,pady=(10,4))
    CTkLabel(vh,text="Visit History",font=FONT_BOLD,text_color=C_TEXT).pack(side="left")
    sv=StringVar(value="")
    vsearch=CTkEntry(vh,width=220,textvariable=sv,fg_color=C_SURFACE,border_color=C_BORDER,text_color=C_TEXT,placeholder_text="Search visits…",placeholder_text_color=C_MUTED)
    vsearch.pack(side="right",padx=(0,4))
    vt=CTkScrollableFrame(vp,fg_color="transparent",height=160,scrollbar_button_color=C_BORDER)
    vt.grid(row=1,column=0,sticky="nsew",padx=PAD,pady=(0,PAD))
    cursor.execute("""SELECT Bookings.BookingID,Services.ServiceName,Bookings.[Date],SlotData.Timings,Hairdressers.HairdresserName,IIf(Bookings.Canceled=True,'Canceled',IIf(Bookings.IsCompleted=True,'Completed','Upcoming')) FROM ((Bookings INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID) INNER JOIN Hairdressers ON Bookings.HairdresserID=Hairdressers.HairdresserID) INNER JOIN SlotData ON Bookings.Slot=SlotData.ID WHERE Bookings.ClientID=? ORDER BY Bookings.[Date] DESC""",(client_id,))
    visits_data=cursor.fetchall()
    def _render_vt():
        clear_frame(vt)
        q=sv.get().lower().strip()
        rows=[r for r in visits_data if not q or q in " ".join(str(x) for x in r).lower()]
        render_table_headers(vt,["Service","Date","Slot","Hairdresser","Status"])
        if not rows: empty_state(vt,"No visits found.",5); return
        for i,r in enumerate(rows):
            _,svc,dv,sv2,hair,st=r
            table_cell(vt,svc,i,0); table_cell(vt,format_date(dv),i,1)
            table_cell(vt,format_slot(sv2),i,2); table_cell(vt,hair,i,3)
            status_badge(vt,st,i,4)
    _ghost_btn(vh,"Search",_render_vt,width=75).pack(side="right",padx=4)
    vsearch.bind("<Return>",lambda e:_render_vt())
    _render_vt()

    # product history
    pp=CTkFrame(panel,fg_color=C_SURFACE2,corner_radius=RADIUS); pp.grid(row=3,column=0,sticky="nsew",padx=PAD,pady=(0,PAD))
    pp.grid_rowconfigure(1,weight=1); pp.grid_columnconfigure(0,weight=1)
    CTkLabel(pp,text="Product Purchases",font=FONT_BOLD,text_color=C_TEXT).pack(anchor="w",padx=PAD,pady=(10,4))
    pt=CTkScrollableFrame(pp,fg_color="transparent",height=140,scrollbar_button_color=C_BORDER)
    pt.pack(fill="both",expand=True,padx=PAD,pady=(0,PAD))
    cursor.execute("""SELECT Products.ProductName,OrderItems.Quantity,OrderItems.PriceAtSale,Orders.OrderDate FROM (Orders INNER JOIN OrderItems ON Orders.OrderID=OrderItems.OrderID) INNER JOIN Products ON OrderItems.ProductID=Products.ProductID WHERE Orders.ClientID=? ORDER BY Orders.OrderDate DESC""",(client_id,))
    ph=cursor.fetchall()
    render_table_headers(pt,["Product","Qty","Price","Date"])
    if not ph: empty_state(pt,"No product purchases.",4)
    else:
        for i,r in enumerate(ph):
            nm,qty,price,dt=r
            table_cell(pt,nm,i,0); table_cell(pt,str(qty),i,1)
            table_cell(pt,f"${safe_float(price):.2f}",i,2); table_cell(pt,format_date(dt),i,3)

def _client_form(panel):
    ne=labeled_entry(panel,"Client Name",1,0)
    ee=labeled_entry(panel,"Email",1,1)
    pe=labeled_entry(panel,"Phone Number",3,0)
    pie=labeled_entry(panel,"Profile Picture Path",3,1)
    return ne,ee,pe,pie

def edit_client_popup(cid):
    overlay,panel,err=overlay_modal(app,"Edit Client")
    cursor.execute("SELECT ClientName,Email,PhoneNumber,ProfilePicture FROM Clients WHERE ClientID=?",(cid,))
    cl=cursor.fetchone()
    if not cl: err.configure(text="Not found."); return
    ne,ee,pe,pie=_client_form(panel)
    ne.insert(0,cl[0] or ""); ee.insert(0,cl[1] or ""); pe.insert(0,cl[2] or ""); pie.insert(0,cl[3] or "")
    def save():
        n=ne.get().strip()
        if not n: err.configure(text="Name required."); return
        cursor.execute("UPDATE Clients SET ClientName=?,Email=?,PhoneNumber=?,ProfilePicture=? WHERE ClientID=?",(n,ee.get().strip(),pe.get().strip(),pie.get().strip(),cid))
        conn.commit(); overlay.destroy(); refresh_clients_page()
    def delete():
        try: cursor.execute("DELETE FROM Clients WHERE ClientID=?",(cid,)); conn.commit()
        except Exception as e: err.configure(text=str(e)); return
        overlay.destroy(); refresh_clients_page()
    modal_buttons(panel,overlay,save,delete,"Save Changes","Delete Client")

def add_client_popup():
    overlay,panel,err=overlay_modal(app,"Add Client")
    ne,ee,pe,pie=_client_form(panel)
    def save():
        n=ne.get().strip()
        if not n: err.configure(text="Name required."); return
        cursor.execute("INSERT INTO Clients(ClientName,Email,PhoneNumber,ProfilePicture,DateJoined) VALUES(?,?,?,?,?)",(n,ee.get().strip(),pe.get().strip(),pie.get().strip(),datetime.now().strftime("%Y-%m-%d")))
        conn.commit(); overlay.destroy(); refresh_clients_page()
    modal_buttons(panel,overlay,save,save_text="Create Client")

# ═══════════════════════════════════════════════════════════════
#  PRODUCTS  (with bulk inventory management)
# ═══════════════════════════════════════════════════════════════

_bulk_edit_mode = False
_bulk_vars = {}   # product_id -> {"name": str, "entry": CTkEntry, "var": StringVar, "check": BoolVar}

def db_products():
    try:
        cursor.execute("SELECT ProductID,ProductName,Price,ProductDescription,StockRemaining,ProductImage FROM Products ORDER BY ProductName")
        return cursor.fetchall()
    except Exception as e:
        print("DB PRODUCTS:", e); return []

def refresh_products_page():
    global product_tile_refs, _bulk_edit_mode, _bulk_vars
    _bulk_edit_mode = False
    _bulk_vars = {}
    product_tile_refs = {}
    clear_frame(products_frame)
    _build_products(products_frame)

def _build_products(parent):
    global _bulk_edit_mode, _bulk_vars

    top = CTkFrame(parent, fg_color="transparent")
    top.pack(fill="x", padx=PAD, pady=(PAD, 8))
    CTkLabel(top, text="Products & Inventory", font=FONT_TITLE, text_color=C_TEXT).pack(side="left")
    ctrl = CTkFrame(top, fg_color="transparent"); ctrl.pack(side="right")

    bulk_btn = _ghost_btn(ctrl, "⚡ Bulk Edit", lambda: _enter_bulk_edit(parent), width=110)
    bulk_btn.pack(side="left", padx=(0,8))
    _gold_btn(ctrl, "+ Add Product", add_product_popup, width=130).pack(side="left")

    data = db_products()
    scroll = CTkScrollableFrame(parent, fg_color="transparent", scrollbar_button_color=C_BORDER)
    scroll.pack(fill="both", expand=True, padx=PAD)

    retail     = [p for p in data if safe_float(p[2]) > 0]
    non_retail = [p for p in data if safe_float(p[2]) <= 0]

    _render_product_section(scroll, "Retail Products", retail)
    if non_retail:
        CTkFrame(scroll, fg_color=C_BORDER, height=1).pack(fill="x", pady=(8,4))
        _render_product_section(scroll, "Non-Retail Stock", non_retail)

def _render_product_section(scroll, title, data):
    if not data: return
    CTkLabel(scroll, text=title, font=FONT_SECTION, text_color=C_GOLD).pack(anchor="w", pady=(12,6))
    grid = CTkFrame(scroll, fg_color="transparent")
    grid.pack(fill="x")
    cols = 3
    for c in range(cols): grid.grid_columnconfigure(c, weight=1, uniform="pr")
    for idx, p in enumerate(data):
        pid,name,price,desc,stock,img = p
        r,c = divmod(idx,cols)
        card = CTkFrame(grid, fg_color=C_SURFACE, corner_radius=RADIUS)
        card.grid(row=r,column=c,padx=10,pady=10,sticky="ew")
        _product_card_content(card, pid, name, price, desc, stock, img)

def _product_card_content(card, pid, name, price, desc, stock, img):
    global product_tile_refs
    clear_frame(card)

    pimg = build_avatar(img, (100,100), circle=False)
    il = CTkLabel(card, image=pimg, text=""); il.image=pimg; il.pack(pady=(16,10))
    CTkLabel(card, text=name, font=FONT_BOLD, text_color=C_TEXT, wraplength=240).pack()
    sp = safe_float(price)
    CTkLabel(card, text=f"${sp:.2f}" if sp>0 else "Non-retail",
             font=("Inter",14,"bold"), text_color=C_GOLD).pack(pady=(4,8))

    # stock row
    sv = safe_int(stock)
    sc = C_SUCCESS if sv>10 else C_WARNING if sv>0 else C_DANGER
    sr = CTkFrame(card, fg_color="transparent"); sr.pack(pady=(0,8))
    CTkButton(sr, text="−", width=32, height=32, corner_radius=8, fg_color="#4a1a1a", hover_color=C_DANGER,
              text_color=C_TEXT, command=lambda id=pid: _adj_stock(id, -1)).pack(side="left",padx=(0,8))
    sl = CTkLabel(sr, text=str(sv), font=FONT_BOLD, text_color=sc, width=44)
    sl.pack(side="left")
    CTkButton(sr, text="+", width=32, height=32, corner_radius=8, fg_color="#1a3a1a", hover_color=C_SUCCESS,
              text_color=C_TEXT, command=lambda id=pid: _adj_stock(id, 1)).pack(side="left",padx=(8,0))

    CTkLabel(card, text=desc or "No description", font=FONT_SMALL, text_color=C_MUTED,
             wraplength=240, justify="center").pack(pady=(0,12))
    CTkFrame(card, fg_color=C_BORDER, height=1).pack(fill="x", padx=16)
    _ghost_btn(card,"Edit", lambda id=pid: edit_product_popup(id), width=80, height=30).pack(pady=12)

    product_tile_refs[pid] = {"stock_label": sl}

def _adj_stock(pid, delta):
    cursor.execute("UPDATE Products SET StockRemaining=StockRemaining+? WHERE ProductID=?", (delta,pid))
    cursor.execute("UPDATE Products SET StockRemaining=0 WHERE ProductID=? AND StockRemaining<0", (pid,))
    conn.commit()
    cursor.execute("SELECT StockRemaining FROM Products WHERE ProductID=?", (pid,))
    r = cursor.fetchone()
    if r and pid in product_tile_refs:
        sv = safe_int(r[0])
        sc = C_SUCCESS if sv>10 else C_WARNING if sv>0 else C_DANGER
        product_tile_refs[pid]["stock_label"].configure(text=str(sv), text_color=sc)

def _enter_bulk_edit(parent):
    """Open bulk inventory management overlay."""
    data = db_products()
    overlay = CTkFrame(app, fg_color="#000000"); overlay.place(relx=0,rely=0,relwidth=1,relheight=1); overlay.lift()
    panel = CTkFrame(overlay, fg_color=C_SURFACE, corner_radius=18)
    panel.place(relx=0.5,rely=0.5,anchor="center",relwidth=0.82,relheight=0.88)
    panel.grid_rowconfigure(2,weight=1); panel.grid_columnconfigure(0,weight=1)

    # title bar
    tb = CTkFrame(panel, fg_color=C_SURFACE2, corner_radius=0, height=56)
    tb.grid(row=0,column=0,sticky="ew"); tb.grid_propagate(False)
    CTkLabel(tb, text="⚡  Bulk Inventory Edit", font=FONT_SECTION, text_color=C_GOLD).pack(side="left",padx=PAD)
    CTkButton(tb,text="✕",width=36,height=36,fg_color="transparent",hover_color=C_DANGER,text_color=C_TEXT_DIM,command=overlay.destroy).pack(side="right",padx=8)

    # bulk action bar
    ab = CTkFrame(panel, fg_color=C_SURFACE2, corner_radius=0)
    ab.grid(row=1,column=0,sticky="ew")
    CTkLabel(ab, text="Bulk action on selected items:", font=FONT_SMALL, text_color=C_MUTED).pack(side="left",padx=PAD,pady=10)
    adj_var = StringVar(value="0")
    adj_entry = CTkEntry(ab, width=70, textvariable=adj_var, fg_color=C_SURFACE, border_color=C_BORDER, text_color=C_TEXT)
    adj_entry.pack(side="left",padx=4)
    _gold_btn(ab,"Adjust Selected", lambda: _bulk_adjust(bulk_rows, adj_var, err_lbl), width=140,height=32).pack(side="left",padx=4)
    CTkLabel(ab,text="  |  Set selected to exact value:",font=FONT_SMALL,text_color=C_MUTED).pack(side="left",padx=(10,4))
    set_var = StringVar(value="")
    set_entry = CTkEntry(ab, width=70, textvariable=set_var, fg_color=C_SURFACE, border_color=C_BORDER, text_color=C_TEXT)
    set_entry.pack(side="left",padx=4)
    _gold_btn(ab,"Set Level", lambda: _bulk_set(bulk_rows, set_var, err_lbl), width=100,height=32).pack(side="left",padx=4)
    _gold_btn(ab,"✓ Apply All",lambda: _bulk_apply(bulk_rows,err_lbl,overlay),width=110,height=32).pack(side="right",padx=PAD)

    err_lbl = CTkLabel(panel,text="",text_color=C_DANGER,font=FONT_SMALL)
    err_lbl.grid(row=3,column=0,pady=4)

    # table
    table = CTkScrollableFrame(panel,fg_color="transparent",scrollbar_button_color=C_BORDER)
    table.grid(row=2,column=0,sticky="nsew",padx=PAD,pady=(4,0))
    for c in range(5): table.grid_columnconfigure(c,weight=1)

    # header
    for ci,h in enumerate(["","Product","Current Stock","New Stock","Price"]):
        CTkLabel(table,text=h,font=FONT_BOLD,text_color=C_MUTED).grid(row=0,column=ci,padx=10,pady=(8,6),sticky="w")
    CTkFrame(table,fg_color=C_BORDER,height=1).grid(row=1,column=0,columnspan=5,sticky="ew",padx=8)

    bulk_rows = {}
    for ri, p in enumerate(data):
        pid,name,price,desc,stock,img = p
        sv = safe_int(stock)
        check_var = BooleanVar(value=False)
        new_var = StringVar(value=str(sv))
        cb = CTkCheckBox(table,text="",variable=check_var,width=24,
                         checkmark_color="#1a1a1a",fg_color=C_GOLD,hover_color=C_GOLD_DARK,border_color=C_BORDER)
        cb.grid(row=ri+2,column=0,padx=10,pady=6,sticky="w")
        CTkLabel(table,text=name,font=FONT_BODY,text_color=C_TEXT).grid(row=ri+2,column=1,padx=10,pady=6,sticky="w")
        sc = C_SUCCESS if sv>10 else C_WARNING if sv>0 else C_DANGER
        CTkLabel(table,text=str(sv),font=FONT_BOLD,text_color=sc).grid(row=ri+2,column=2,padx=10,pady=6,sticky="w")
        entry = CTkEntry(table,width=90,textvariable=new_var,fg_color=C_SURFACE,border_color=C_GOLD,text_color=C_TEXT)
        entry.grid(row=ri+2,column=3,padx=10,pady=6,sticky="w")
        sp = safe_float(price)
        CTkLabel(table,text=f"${sp:.2f}" if sp>0 else "—",font=FONT_SMALL,text_color=C_MUTED).grid(row=ri+2,column=4,padx=10,pady=6,sticky="w")
        bulk_rows[pid]={"name":name,"var":new_var,"check":check_var,"current":sv}

def _bulk_adjust(rows, adj_var, err):
    try: delta = int(adj_var.get().strip())
    except: err.configure(text="Enter a valid integer for adjustment."); return
    err.configure(text="")
    for pid,row in rows.items():
        if row["check"].get():
            new_val = max(0, row["current"] + delta)
            row["var"].set(str(new_val))

def _bulk_set(rows, set_var, err):
    try: val = int(set_var.get().strip())
    except: err.configure(text="Enter a valid integer for set level."); return
    if val < 0: err.configure(text="Stock cannot be negative."); return
    err.configure(text="")
    for pid,row in rows.items():
        if row["check"].get():
            row["var"].set(str(val))

def _bulk_apply(rows, err, overlay):
    err.configure(text="")
    updates = []
    for pid, row in rows.items():
        try: new_val = int(row["var"].get().strip())
        except: err.configure(text=f"Invalid value for {row['name']}."); return
        if new_val < 0: err.configure(text=f"Stock for {row['name']} cannot be negative."); return
        updates.append((new_val, pid))
    for new_val, pid in updates:
        cursor.execute("UPDATE Products SET StockRemaining=? WHERE ProductID=?", (new_val, pid))
    conn.commit()
    overlay.destroy()
    refresh_products_page()

def _product_form(panel):
    ne=labeled_entry(panel,"Product Name",1,0)
    pre=labeled_entry(panel,"Price",1,1)
    de=labeled_entry(panel,"Description",3,0)
    se=labeled_entry(panel,"Stock",3,1)
    ie=labeled_entry(panel,"Image Path",5,0)
    return ne,pre,de,se,ie

def edit_product_popup(pid):
    overlay,panel,err=overlay_modal(app,"Edit Product",width=720,height=540)
    try:
        cursor.execute("SELECT ProductID,ProductName,Price,ProductDescription,StockRemaining,ProductImage FROM Products WHERE ProductID=?",(pid,))
        p=cursor.fetchone()
    except Exception as e: err.configure(text=str(e)); return
    if not p: err.configure(text="Not found."); return
    _,name,price,desc,stock,img=p
    ne,pre,de,se,ie=_product_form(panel)
    ne.insert(0,name or ""); pre.insert(0,str(price or "")); de.insert(0,desc or "")
    se.insert(0,str(stock or "")); ie.insert(0,img or "")
    def save():
        n=ne.get().strip()
        prc=safe_float(pre.get().strip(),None); stk=safe_int(se.get().strip(),None)
        if not n: err.configure(text="Name required."); return
        if prc is None: err.configure(text="Price must be a number."); return
        if stk is None: err.configure(text="Stock must be a number."); return
        cursor.execute("UPDATE Products SET ProductName=?,Price=?,[ProductDesctiption]=?,StockRemaining=?,ProductImage=? WHERE ProductID=?",(n,prc,de.get().strip(),stk,ie.get().strip(),pid))
        conn.commit(); overlay.destroy(); refresh_products_page()
    def delete():
        try: cursor.execute("DELETE FROM Products WHERE ProductID=?",(pid,)); conn.commit()
        except Exception as e: err.configure(text=str(e)); return
        overlay.destroy(); refresh_products_page()
    modal_buttons(panel,overlay,save,delete,"Save Changes","Delete Product")

def add_product_popup():
    overlay,panel,err=overlay_modal(app,"Add Product",width=720,height=540)
    ne,pre,de,se,ie=_product_form(panel)
    def save():
        n=ne.get().strip()
        prc=safe_float(pre.get().strip(),None); stk=safe_int(se.get().strip(),None)
        if not n: err.configure(text="Name required."); return
        if prc is None: err.configure(text="Price must be a number."); return
        if stk is None: err.configure(text="Stock must be a number."); return
        cursor.execute("INSERT INTO Products(ProductName,Price,ProductDescription,StockRemaining,ProductImage) VALUES(?,?,?,?,?)",(n,prc,de.get().strip(),stk,ie.get().strip()))
        conn.commit(); overlay.destroy(); refresh_products_page()
    modal_buttons(panel,overlay,save,save_text="Create Product")

# ═══════════════════════════════════════════════════════════════
#  HAIRDRESSER SCHEDULE
# ═══════════════════════════════════════════════════════════════

def refresh_hairdresser_bookings_page():
    clear_frame(hairdresser_bookings_frame)
    _build_schedule_selector(hairdresser_bookings_frame)

def _build_schedule_selector(parent):
    CTkLabel(parent,text="Hairdresser Schedule",font=FONT_TITLE,text_color=C_TEXT).pack(padx=PAD,pady=(PAD,8),anchor="w")
    cursor.execute("SELECT HairdresserID,HairdresserName,ProfilePicture FROM Hairdressers ORDER BY HairdresserName")
    data=cursor.fetchall()
    scroll=CTkScrollableFrame(parent,fg_color="transparent",scrollbar_button_color=C_BORDER)
    scroll.pack(fill="both",expand=True,padx=PAD)
    cols=4
    for c in range(cols): scroll.grid_columnconfigure(c,weight=1,uniform="sc")
    for idx,h in enumerate(data):
        hid,name,img=h; r,c=divmod(idx,cols)
        card=CTkFrame(scroll,fg_color=C_SURFACE,corner_radius=RADIUS)
        card.grid(row=r,column=c,padx=10,pady=10,sticky="ew")
        av=build_avatar(img,(90,90),circle=True)
        il=CTkLabel(card,image=av,text=""); il.image=av; il.pack(pady=(18,8))
        CTkLabel(card,text=name,font=FONT_BOLD,text_color=C_TEXT,wraplength=180).pack(pady=(0,12))
        _gold_btn(card,"Open Schedule",lambda id=hid,n=name: _open_schedule(id,n),width=140,height=32).pack(pady=(0,18))

def _open_schedule(hid, hname):
    global selected_hairdresser_id, selected_hairdresser_name
    selected_hairdresser_id=hid; selected_hairdresser_name=hname
    clear_frame(hairdresser_bookings_frame)
    _build_schedule_view(hairdresser_bookings_frame, hid, hname)

def _build_schedule_view(parent, hid, hname):
    top=CTkFrame(parent,fg_color="transparent"); top.pack(fill="x",padx=PAD,pady=(PAD,8))
    _ghost_btn(top,"← Back",refresh_hairdresser_bookings_page,width=90).pack(side="left",padx=(0,10))
    CTkLabel(top,text=f"{hname} — Schedule",font=FONT_TITLE,text_color=C_TEXT).pack(side="left")

    bar=CTkFrame(parent,fg_color="transparent"); bar.pack(fill="x",padx=PAD,pady=(0,6))
    btns={}
    def activate(k):
        for bk,b in btns.items():
            b.configure(fg_color=C_GOLD if bk==k else "transparent",
                        text_color="#1a1a1a" if bk==k else C_TEXT_DIM)

    table_holder=CTkScrollableFrame(parent,fg_color="transparent",scrollbar_button_color=C_BORDER)
    table_holder.pack(fill="both",expand=True,padx=PAD,pady=(0,PAD))

    def load(mode):
        clear_frame(table_holder)
        if mode=="upcoming":
            cursor.execute(_BOOKING_SELECT.replace("INNER JOIN SlotData","INNER JOIN SlotData").replace("SELECT Bookings.BookingID,","SELECT Bookings.BookingID,").replace(
                "INNER JOIN SlotData    ON Bookings.Slot=SlotData.ID",
                "INNER JOIN SlotData    ON Bookings.Slot=SlotData.ID"
            ) + "WHERE Bookings.Canceled=False AND Bookings.HairdresserID=? AND DateValue(Bookings.[Date])>=Date() AND DateValue(Bookings.[Date])<=Date()+1 ORDER BY Bookings.[Date],Bookings.Slot",(hid,))
        elif mode=="all":
            cursor.execute(_BOOKING_SELECT + "WHERE Bookings.Canceled=False AND Bookings.HairdresserID=? ORDER BY Bookings.[Date],Bookings.Slot",(hid,))
        else:
            cursor.execute("""
                SELECT Bookings.BookingID,Clients.ClientName,Services.ServiceName,Bookings.[Date],SlotData.Timings,Hairdressers.HairdresserName,'Canceled'
                FROM (((Bookings INNER JOIN Clients ON Bookings.ClientID=Clients.ClientID) INNER JOIN Services ON Bookings.ServiceID=Services.ServiceID) INNER JOIN Hairdressers ON Bookings.HairdresserID=Hairdressers.HairdresserID) INNER JOIN SlotData ON Bookings.Slot=SlotData.ID
                WHERE Bookings.Canceled=True AND Bookings.HairdresserID=? ORDER BY Bookings.[Date],Bookings.Slot
            """,(hid,))
        rows=cursor.fetchall()
        render_table_headers(table_holder,["Client","Service","Date","Slot","Status",""])
        if not rows: empty_state(table_holder,"No bookings found.",6); return
        for i,r in enumerate(rows):
            bid,cl,svc,dv,sv,hair,st=r
            table_cell(table_holder,cl,i,0); table_cell(table_holder,svc,i,1)
            table_cell(table_holder,format_date(dv,"%d/%m/%Y"),i,2); table_cell(table_holder,format_slot(sv),i,3)
            status_badge(table_holder,st,i,4)
            _ghost_btn(table_holder,"Edit",lambda bid=bid: edit_booking_popup(bid),width=60,height=28).grid(row=i+2,column=5,padx=8,pady=5)

    b1=_ghost_btn(bar,"Upcoming",lambda:[activate("u"),load("upcoming")],width=110)
    b2=_ghost_btn(bar,"All",lambda:[activate("a"),load("all")],width=80)
    b3=_ghost_btn(bar,"Canceled",lambda:[activate("c"),load("canceled")],width=110)
    b1.configure(fg_color=C_GOLD,text_color="#1a1a1a")
    for b in [b1,b2,b3]: b.pack(side="left",padx=(0,6))
    btns.update({"u":b1,"a":b2,"c":b3})
    load("upcoming")

# ═══════════════════════════════════════════════════════════════
#  ORDERS
# ═══════════════════════════════════════════════════════════════

def refresh_orders_page():
    clear_frame(orders_frame)
    _build_orders(orders_frame)

def _build_orders(parent):
    top=CTkFrame(parent,fg_color="transparent"); top.pack(fill="x",padx=PAD,pady=(PAD,8))
    CTkLabel(top,text="Orders & Transactions",font=FONT_TITLE,text_color=C_TEXT).pack(side="left")
    _gold_btn(top,"+ Add Transaction",add_order_popup,width=160).pack(side="right")

    cursor.execute("SELECT OrderID,ClientID,OrderDate,PaymentMethod,TotalAmount FROM Orders ORDER BY OrderID DESC")
    rows=cursor.fetchall()

    wrap=CTkScrollableFrame(parent,fg_color="transparent",scrollbar_button_color=C_BORDER)
    wrap.pack(fill="both",expand=True,padx=PAD,pady=(0,PAD))
    headers=["Order #","Client","Date","Payment","Items","Total",""]
    render_table_headers(wrap,headers,[1,2,2,1,1,1,1])
    if not rows: empty_state(wrap,"No transactions found.",7); return
    for i,r in enumerate(rows):
        oid,cid,dt,pay,total=r
        cursor.execute("SELECT ClientName FROM Clients WHERE ClientID=?",(cid,))
        cr=cursor.fetchone(); cname=cr[0] if cr else "—"
        cursor.execute("SELECT COUNT(*) FROM OrderItems WHERE OrderID=?",(oid,))
        items=safe_int(cursor.fetchone()[0])
        table_cell(wrap,f"#{oid}",i,0,bold=True,color=C_GOLD)
        table_cell(wrap,cname,i,1); table_cell(wrap,safe_text(dt),i,2)
        table_cell(wrap,safe_text(pay),i,3); table_cell(wrap,str(items),i,4)
        table_cell(wrap,f"${safe_float(total):.2f}",i,5,color=C_SUCCESS,bold=True)
        _ghost_btn(wrap,"Details",lambda id=oid: _order_details_popup(id),width=75,height=28).grid(row=i+2,column=6,padx=8,pady=5)

def _order_details_popup(oid):
    overlay=CTkFrame(app,fg_color="#000000"); overlay.place(relx=0,rely=0,relwidth=1,relheight=1); overlay.lift()
    panel=CTkFrame(overlay,fg_color=C_SURFACE,corner_radius=18)
    panel.place(relx=0.5,rely=0.5,anchor="center",relwidth=0.7,relheight=0.75)
    panel.grid_rowconfigure(1,weight=1); panel.grid_columnconfigure(0,weight=1)

    cursor.execute("SELECT OrderID,ClientID,OrderDate,PaymentMethod,TotalAmount FROM Orders WHERE OrderID=?",(oid,))
    r=cursor.fetchone()
    if not r: CTkLabel(panel,text="Order not found.",text_color=C_DANGER).pack(pady=20); return
    _,cid,dt,pay,total=r
    cursor.execute("SELECT ClientName FROM Clients WHERE ClientID=?",(cid,)); cr=cursor.fetchone()
    cname=cr[0] if cr else "—"

    tb=CTkFrame(panel,fg_color=C_SURFACE2,corner_radius=0,height=56)
    tb.grid(row=0,column=0,sticky="ew"); tb.grid_propagate(False)
    CTkLabel(tb,text=f"Order #{oid}",font=FONT_SECTION,text_color=C_GOLD).pack(side="left",padx=PAD)
    CTkButton(tb,text="✕",width=36,height=36,fg_color="transparent",hover_color=C_DANGER,text_color=C_TEXT_DIM,command=overlay.destroy).pack(side="right",padx=8)

    body=CTkFrame(panel,fg_color="transparent"); body.grid(row=1,column=0,sticky="nsew",padx=PAD,pady=PAD)
    body.grid_rowconfigure(1,weight=1); body.grid_columnconfigure(0,weight=1)
    meta=CTkFrame(body,fg_color=C_SURFACE2,corner_radius=10); meta.pack(fill="x",pady=(0,10))
    for txt in [f"Client: {cname}",f"Date: {safe_text(dt)}",f"Payment: {safe_text(pay)}"]:
        CTkLabel(meta,text=txt,font=FONT_BODY,text_color=C_TEXT).pack(anchor="w",padx=PAD,pady=3)
    CTkLabel(meta,text=f"Total: ${safe_float(total):.2f}",font=("Inter",16,"bold"),text_color=C_SUCCESS).pack(anchor="w",padx=PAD,pady=(0,10))

    table=CTkScrollableFrame(body,fg_color="transparent",scrollbar_button_color=C_BORDER)
    table.pack(fill="both",expand=True)
    render_table_headers(table,["Product","Qty","Unit Price","Line Total"])
    cursor.execute("SELECT ProductID,Quantity,PriceAtSale FROM OrderItems WHERE OrderID=? ORDER BY ID",(oid,))
    items=cursor.fetchall()
    if not items: empty_state(table,"No items.",4)
    for i,item in enumerate(items):
        pid,qty,uprice=item
        cursor.execute("SELECT ProductName FROM Products WHERE ProductID=?",(pid,))
        pr=cursor.fetchone(); pname=pr[0] if pr else "—"
        table_cell(table,pname,i,0); table_cell(table,str(qty),i,1)
        table_cell(table,f"${safe_float(uprice):.2f}",i,2)
        table_cell(table,f"${safe_float(qty)*safe_float(uprice):.2f}",i,3,color=C_SUCCESS)

def _load_order_refs():
    cursor.execute("SELECT ClientID,ClientName FROM Clients ORDER BY ClientName")
    cm={r[1]:r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT ProductID,ProductName,Price,StockRemaining FROM Products ORDER BY ProductName")
    pm={}; dv=[]
    for r in cursor.fetchall():
        pid,pname,price,stock=r; pid=int(pid); stock=safe_int(stock)
        dn=f"{pname} [Out of stock]" if stock<=0 else pname
        pm[dn]={"ProductID":pid,"ProductName":pname,"Price":safe_float(price),"StockRemaining":stock,"IsOut":stock<=0}
        dv.append(dn)
    return cm,pm,dv

def add_order_popup():
    overlay=CTkFrame(app,fg_color="#000000"); overlay.place(relx=0,rely=0,relwidth=1,relheight=1); overlay.lift()
    panel=CTkFrame(overlay,fg_color=C_SURFACE,corner_radius=18)
    panel.place(relx=0.5,rely=0.5,anchor="center",relwidth=0.84,relheight=0.88)
    panel.grid_rowconfigure(2,weight=1); panel.grid_columnconfigure(0,weight=1)
    cm,pm,dv=_load_order_refs(); order_lines=[]
    err=CTkLabel(panel,text="",text_color=C_DANGER,font=FONT_SMALL)
    succ=CTkLabel(panel,text="",text_color=C_SUCCESS,font=FONT_SMALL)

    tb=CTkFrame(panel,fg_color=C_SURFACE2,corner_radius=0,height=56); tb.grid(row=0,column=0,sticky="ew"); tb.grid_propagate(False)
    CTkLabel(tb,text="New Transaction",font=FONT_SECTION,text_color=C_GOLD).pack(side="left",padx=PAD)
    CTkButton(tb,text="✕",width=36,height=36,fg_color="transparent",hover_color=C_DANGER,text_color=C_TEXT_DIM,command=overlay.destroy).pack(side="right",padx=8)

    if not cm:
        CTkLabel(panel,text="No clients. Add a client first.",text_color=C_DANGER,font=FONT_BODY).pack(pady=40); return
    if not pm:
        CTkLabel(panel,text="No products. Add a product first.",text_color=C_DANGER,font=FONT_BODY).pack(pady=40); return

    form=CTkFrame(panel,fg_color="transparent"); form.grid(row=1,column=0,sticky="ew",padx=PAD,pady=(PAD,0))
    CTkLabel(form,text="Client",font=FONT_SMALL,text_color=C_TEXT_DIM).grid(row=0,column=0,sticky="w",padx=8,pady=(0,3))
    cb_c=CTkComboBox(form,values=list(cm.keys()),width=240,fg_color=C_SURFACE2,border_color=C_BORDER,text_color=C_TEXT,button_color=C_GOLD,dropdown_fg_color=C_SURFACE2)
    cb_c.grid(row=1,column=0,padx=8,pady=(0,PAD),sticky="w"); cb_c.set(list(cm.keys())[0])
    CTkLabel(form,text="Date & Time",font=FONT_SMALL,text_color=C_TEXT_DIM).grid(row=0,column=1,sticky="w",padx=8,pady=(0,3))
    dte=CTkEntry(form,width=200,fg_color=C_SURFACE2,border_color=C_BORDER,text_color=C_TEXT)
    dte.grid(row=1,column=1,padx=8,pady=(0,PAD),sticky="w"); dte.insert(0,datetime.now().strftime("%Y-%m-%d %H:%M"))
    CTkLabel(form,text="Payment",font=FONT_SMALL,text_color=C_TEXT_DIM).grid(row=0,column=2,sticky="w",padx=8,pady=(0,3))
    pay_seg=CTkSegmentedButton(form,values=["Cash","Card"],selected_color=C_GOLD,selected_hover_color=C_GOLD_DARK,unselected_color=C_SURFACE,fg_color=C_SURFACE2,text_color=C_TEXT)
    pay_seg.grid(row=1,column=2,padx=8,pady=(0,PAD),sticky="w"); pay_seg.set("Cash")

    items_sec=CTkFrame(panel,fg_color=C_SURFACE2,corner_radius=RADIUS); items_sec.grid(row=2,column=0,sticky="nsew",padx=PAD,pady=(0,PAD))
    items_sec.grid_rowconfigure(1,weight=1); items_sec.grid_columnconfigure(0,weight=1)
    ih=CTkFrame(items_sec,fg_color="transparent"); ih.pack(fill="x",padx=PAD,pady=(10,0))
    CTkLabel(ih,text="Order Items",font=FONT_BOLD,text_color=C_TEXT).pack(side="left")
    total_lbl=CTkLabel(ih,text="Total: $0.00",font=("Inter",16,"bold"),text_color=C_SUCCESS); total_lbl.pack(side="right")

    rows_holder=CTkScrollableFrame(items_sec,fg_color="transparent",scrollbar_button_color=C_BORDER)
    rows_holder.pack(fill="both",expand=True,padx=PAD,pady=8)

    def calc_total():
        t=0.0
        for ln in order_lines:
            sel=ln["pb"].get()
            if sel in pm:
                try: q=int(ln["qe"].get().strip())
                except: q=0
                if q>0: t+=q*pm[sel]["Price"]
        total_lbl.configure(text=f"Total: ${t:.2f}")

    def add_line():
        rw=CTkFrame(rows_holder,fg_color=C_SURFACE,corner_radius=8); rw.pack(fill="x",pady=4)
        rw.grid_columnconfigure(0,weight=3); rw.grid_columnconfigure(1,weight=1)
        rw.grid_columnconfigure(2,weight=1); rw.grid_columnconfigure(3,weight=1); rw.grid_columnconfigure(4,weight=0)
        pb=CTkComboBox(rw,values=dv,width=260,fg_color=C_SURFACE2,border_color=C_BORDER,text_color=C_TEXT,button_color=C_GOLD,dropdown_fg_color=C_SURFACE2)
        pb.grid(row=0,column=0,padx=8,pady=8,sticky="ew")
        qe=CTkEntry(rw,width=70,placeholder_text="Qty",fg_color=C_SURFACE2,border_color=C_BORDER,text_color=C_TEXT,placeholder_text_color=C_MUTED)
        qe.grid(row=0,column=1,padx=8,pady=8)
        sl=CTkLabel(rw,text="Stock: —",font=FONT_SMALL,text_color=C_MUTED); sl.grid(row=0,column=2,padx=8)
        pl=CTkLabel(rw,text="$0.00",font=FONT_SMALL,text_color=C_GOLD); pl.grid(row=0,column=3,padx=8)
        def upd(choice):
            if choice in pm:
                info=pm[choice]; stk=info["StockRemaining"]; pr=info["Price"]
                sl.configure(text="OUT" if stk<=0 else f"Stock: {stk}",text_color=C_DANGER if stk<=0 else C_MUTED)
                pl.configure(text=f"${pr:.2f}")
                qe.configure(state="disabled" if stk<=0 else "normal")
            calc_total()
        def rm():
            if len(order_lines)<=1: err.configure(text="Need at least one item."); return
            rw.destroy(); order_lines[:] = [l for l in order_lines if l["rw"]!=rw]; calc_total()
        pb.configure(command=upd); qe.bind("<KeyRelease>",lambda e: calc_total())
        CTkButton(rw,text="✕",width=28,height=28,fg_color="transparent",hover_color=C_DANGER,text_color=C_MUTED,command=rm).grid(row=0,column=4,padx=8)
        ln={"rw":rw,"pb":pb,"qe":qe,"pm":pm}; order_lines.append(ln)
        if dv: pb.set(dv[0]); upd(dv[0])

    bf=CTkFrame(items_sec,fg_color="transparent"); bf.pack(fill="x",padx=PAD,pady=(0,8))
    _ghost_btn(bf,"+ Add Item",add_line,width=110,height=30).pack(side="left")
    err.pack(side="left",padx=10)

    add_line()  # start with one row

    def save():
        err.configure(text="")
        try:
            cname=cb_c.get().strip()
            if cname not in cm: err.configure(text="Select a valid client."); return
            try: odt=datetime.strptime(dte.get().strip(),"%Y-%m-%d %H:%M")
            except: err.configure(text="Date format: YYYY-MM-DD HH:MM"); return
            pay=pay_seg.get().strip().capitalize()
            merged={}; total=0.0
            for ln in order_lines:
                sel=ln["pb"].get().strip()
                if sel not in pm: err.configure(text="Select a valid product."); return
                info=pm[sel]; pid2=info["ProductID"]; stk=info["StockRemaining"]; pr=info["Price"]
                try: q=int(ln["qe"].get().strip())
                except: err.configure(text=f"Invalid qty for {info['ProductName']}."); return
                if q<=0: err.configure(text=f"Qty must be > 0 for {info['ProductName']}."); return
                if stk<=0: err.configure(text=f"{info['ProductName']} is out of stock."); return
                merged[pid2]=merged.get(pid2,{"name":info["ProductName"],"price":pr,"stock":stk,"qty":0})
                merged[pid2]["qty"]+=q
            for info in merged.values():
                if info["qty"]>info["stock"]: err.configure(text=f"Not enough stock for {info['name']}."); return
                total+=info["qty"]*info["price"]
            cursor.execute("INSERT INTO Orders(ClientID,OrderDate,PaymentMethod,TotalAmount) VALUES(?,?,?,?)",(int(cm[cname]),odt,pay,float(total)))
            conn.commit()
            cursor.execute("SELECT MAX(OrderID) FROM Orders"); new_oid=safe_int(cursor.fetchone()[0])
            for pid2,info in merged.items():
                cursor.execute("INSERT INTO OrderItems(OrderID,ProductID,Quantity,PriceAtSale) VALUES(?,?,?,?)",(new_oid,pid2,info["qty"],info["price"]))
                cursor.execute("UPDATE Products SET StockRemaining=StockRemaining-? WHERE ProductID=?",(info["qty"],pid2))
            conn.commit()
            # success confirmation
            done=CTkFrame(app,fg_color="#000000"); done.place(relx=0,rely=0,relwidth=1,relheight=1); done.lift()
            dp=CTkFrame(done,fg_color=C_SURFACE,corner_radius=18,width=340,height=160); dp.place(relx=0.5,rely=0.5,anchor="center")
            CTkLabel(dp,text="✓  Transaction Complete",font=FONT_SECTION,text_color=C_SUCCESS).pack(pady=(28,6))
            CTkLabel(dp,text=f"Order #{new_oid} saved  •  Total ${total:.2f}",font=FONT_BODY,text_color=C_MUTED).pack()
            def close_all(): done.destroy(); overlay.destroy(); refresh_orders_page(); refresh_products_page()
            _gold_btn(dp,"OK",close_all,width=100).pack(pady=16)
        except Exception as e: print("SAVE ORDER ERROR:",e); err.configure(text="Could not save order.")

    bot=CTkFrame(panel,fg_color="transparent"); bot.grid(row=3,column=0,pady=(0,PAD))
    succ.pack()
    _gold_btn(bot,"Confirm & Pay",save,width=160,height=40).pack(side="left",padx=8)
    _ghost_btn(bot,"Cancel",overlay.destroy,width=120,height=40).pack(side="left",padx=8)

# ═══════════════════════════════════════════════════════════════
#  FINANCIALS TAB
# ═══════════════════════════════════════════════════════════════

_fin_expense_search = None
_fin_cat_var = None

def refresh_financials_page():
    clear_frame(financials_frame)
    _build_financials(financials_frame)

def _build_financials(parent):
    global _fin_expense_search, _fin_cat_var

    scroll=CTkScrollableFrame(parent,fg_color=C_BG,scrollbar_button_color=C_BORDER)
    scroll.pack(fill="both",expand=True)

    # ── Header ──
    hdr=CTkFrame(scroll,fg_color="transparent"); hdr.pack(fill="x",padx=PAD,pady=(PAD,8))
    CTkLabel(hdr,text="Financials",font=FONT_TITLE,text_color=C_TEXT).pack(side="left")
    _gold_btn(hdr, "Export P&L", export_pl_excel, width=120).pack(side="right", padx=(8,0))
    _gold_btn(hdr, "+ Add Expense", add_expense_popup, width=140).pack(side="right")

    # ── KPI row ──
    rev=db_total_revenue_alltime(); costs=db_total_costs_alltime()
    net=rev-costs; margin=round((net/rev)*100,1) if rev>0 else 0.0
    svc_m,prod_m=db_revenue_by_category()

    kr=CTkFrame(scroll,fg_color="transparent"); kr.pack(fill="x",padx=PAD,pady=(0,6))
    for c in range(4): kr.grid_columnconfigure(c,weight=1)
    kpi_card(kr,"Total Revenue (All Time)", f"${rev:,.2f}",   "services + products",  C_GOLD,    0,0)
    kpi_card(kr,"Total Costs (All Time)",   f"${costs:,.2f}", "logged expenses",       C_DANGER,  0,1)
    kpi_card(kr,"Net Profit (All Time)",    f"${net:,.2f}",   "revenue minus costs",   C_SUCCESS, 0,2)
    kpi_card(kr,"Profit Margin",            f"{margin}%",     "all time",              "#9b7fe8", 0,3)

    # ── This month breakdown ──
    mb=CTkFrame(scroll,fg_color="transparent"); mb.pack(fill="x",padx=PAD,pady=(0,6))
    for c in range(3): mb.grid_columnconfigure(c,weight=1)
    kpi_card(mb,"Service Revenue (Month)",  f"${svc_m:,.2f}",  "completed bookings",   C_GOLD,   0,0)
    kpi_card(mb,"Product Revenue (Month)",  f"${prod_m:,.2f}", "product orders",        C_SUCCESS,0,1)
    try:
        cursor.execute("SELECT SUM(Amount) FROM Expenses WHERE Month(DateTime)=Month(Date()) AND Year(DateTime)=Year(Date())")
        month_costs=safe_float(cursor.fetchone()[0])
    except: month_costs=0.0
    kpi_card(mb,"Costs (This Month)",        f"${month_costs:,.2f}","logged this month",   C_DANGER, 0,2)

    # ── P&L Chart ──
    pl_card=CTkFrame(scroll,fg_color=C_SURFACE,corner_radius=RADIUS)
    pl_card.pack(fill="x",padx=PAD,pady=(0,8))
    CTkLabel(pl_card,text="Monthly P&L  —  Last 6 Months",font=FONT_BOLD,text_color=C_TEXT).pack(anchor="w",padx=PAD,pady=(PAD,4))
    pl_frame=CTkFrame(pl_card,fg_color="transparent",height=220); pl_frame.pack(fill="x",padx=PAD,pady=(0,PAD))
    _draw_pl_chart(pl_frame)

    # ── Revenue breakdown donut ──
    split_row=CTkFrame(scroll,fg_color="transparent"); split_row.pack(fill="x",padx=PAD,pady=(0,8))
    split_row.grid_columnconfigure(0,weight=1); split_row.grid_columnconfigure(1,weight=1)

    rd_card=CTkFrame(split_row,fg_color=C_SURFACE,corner_radius=RADIUS)
    rd_card.grid(row=0,column=0,padx=(0,6),sticky="nsew")
    CTkLabel(rd_card,text="Revenue Sources (This Month)",font=FONT_BOLD,text_color=C_TEXT).pack(anchor="w",padx=PAD,pady=(PAD,4))
    rd_f=CTkFrame(rd_card,fg_color="transparent",height=200); rd_f.pack(fill="x",padx=PAD,pady=(0,PAD))
    _draw_revenue_split(rd_f,svc_m,prod_m)

    exp_cat_card=CTkFrame(split_row,fg_color=C_SURFACE,corner_radius=RADIUS)
    exp_cat_card.grid(row=0,column=1,padx=(6,0),sticky="nsew")
    CTkLabel(exp_cat_card,text="Expense Breakdown (All Time)",font=FONT_BOLD,text_color=C_TEXT).pack(anchor="w",padx=PAD,pady=(PAD,4))
    ec_f=CTkFrame(exp_cat_card,fg_color="transparent",height=200); ec_f.pack(fill="x",padx=PAD,pady=(0,PAD))
    _draw_expense_cats(ec_f)

    # ── Expense log ──
    exp_card=CTkFrame(scroll,fg_color=C_SURFACE,corner_radius=RADIUS)
    exp_card.pack(fill="x",padx=PAD,pady=(0,PAD))

    eh=CTkFrame(exp_card,fg_color="transparent"); eh.pack(fill="x",padx=PAD,pady=(PAD,6))
    CTkLabel(eh,text="Expense Log",font=FONT_BOLD,text_color=C_TEXT).pack(side="left")

    if _fin_expense_search is None: _fin_expense_search=StringVar(value="")
    if _fin_cat_var is None: _fin_cat_var=StringVar(value="All")

    se=CTkEntry(eh,width=180,textvariable=_fin_expense_search,fg_color=C_SURFACE2,border_color=C_BORDER,text_color=C_TEXT,placeholder_text="Search…",placeholder_text_color=C_MUTED)
    se.pack(side="right",padx=(4,0))
    cats=["All"]+EXPENSE_CATS
    cf=CTkComboBox(eh,values=cats,variable=_fin_cat_var,width=180,fg_color=C_SURFACE2,border_color=C_BORDER,text_color=C_TEXT,button_color=C_GOLD,dropdown_fg_color=C_SURFACE2)
    cf.pack(side="right",padx=4)
    _ghost_btn(eh,"Search",lambda: _reload_expense_table(exp_table),width=80).pack(side="right",padx=4)

    exp_table=CTkScrollableFrame(exp_card,fg_color="transparent",height=280,scrollbar_button_color=C_BORDER)
    exp_table.pack(fill="x",padx=PAD,pady=(0,PAD))
    _reload_expense_table(exp_table)
    se.bind("<Return>",lambda e:_reload_expense_table(exp_table))

def _draw_pl_chart(parent):
    clear_frame(parent)
    data=db_monthly_pl(6)
    if not data: CTkLabel(parent,text="No data",text_color=C_MUTED,font=FONT_BODY).pack(expand=True); return
    labels=[d[0] for d in data]
    rev=[d[1] for d in data]
    costs=[d[2] for d in data]
    x=range(len(labels))
    fig,ax=_chart_fig(9,2.8)
    w=0.35
    bars_r=ax.bar([i-w/2 for i in x],rev,  width=w,color=C_GOLD,  label="Revenue",  alpha=0.9)
    bars_c=ax.bar([i+w/2 for i in x],costs,width=w,color=C_DANGER,label="Costs",    alpha=0.9)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels,color=C_MUTED,fontsize=9)
    ax.tick_params(axis="y",colors=C_MUTED)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_:f"${v:,.0f}"))
    ax.set_title("Revenue vs Costs",color=C_TEXT,fontsize=12,pad=8)
    leg=ax.legend(facecolor=C_SURFACE2,labelcolor=C_TEXT,fontsize=9)
    for bar in bars_r:
        h=bar.get_height()
        if h>0: ax.text(bar.get_x()+bar.get_width()/2,h+1,f"${h:,.0f}",ha="center",color=C_MUTED,fontsize=7)
    plt.tight_layout(pad=1.0)
    embed_chart(fig,parent)

def _draw_revenue_split(parent, svc, prod):
    clear_frame(parent)
    if svc+prod==0: CTkLabel(parent,text="No revenue this month",text_color=C_MUTED,font=FONT_BODY).pack(expand=True); return
    fig,ax=_chart_fig(4,2.6)
    ax.pie([svc,prod],labels=[f"Services\n${svc:.2f}",f"Products\n${prod:.2f}"],
           colors=[C_GOLD,C_SUCCESS],autopct="%1.0f%%",startangle=90,
           pctdistance=0.75,wedgeprops=dict(width=0.5),textprops={"color":C_MUTED,"fontsize":9})
    plt.tight_layout(pad=0.8)
    embed_chart(fig,parent)

def _draw_expense_cats(parent):
    clear_frame(parent)
    try:
        cursor.execute("SELECT Category,SUM(Amount) FROM Expenses GROUP BY Category ORDER BY SUM(Amount) DESC")
        data=cursor.fetchall()
    except: data=[]
    if not data: CTkLabel(parent,text="No expenses logged yet",text_color=C_MUTED,font=FONT_BODY).pack(expand=True); return
    cats=[r[0] for r in data]; amts=[safe_float(r[1]) for r in data]
    colors=[C_DANGER,C_WARNING,C_GOLD,C_SUCCESS,"#9b7fe8"]
    fig,ax=_chart_fig(4,2.6)
    ax.pie(amts,labels=cats,colors=colors[:len(cats)],autopct="%1.0f%%",startangle=90,
           pctdistance=0.72,wedgeprops=dict(width=0.5),textprops={"color":C_MUTED,"fontsize":8})
    plt.tight_layout(pad=0.8)
    embed_chart(fig,parent)

def _reload_expense_table(table):
    clear_frame(table)

    search = _fin_expense_search.get() if _fin_expense_search else ""
    cat = _fin_cat_var.get() if _fin_cat_var else "All"

    data = db_expenses(search, cat)

    headers = ["Date", "Category", "Title", "Amount", "Notes", ""]
    render_table_headers(table, headers, [1, 2, 3, 1, 2, 1])

    if not data:
        empty_state(table, "No expenses found.", 6)
        return

    for i, r in enumerate(data):
        eid, cat, title, amt, dt, notes = r

        table_cell(table, format_date(dt), i, 0)
        table_cell(table, cat, i, 1, color=C_WARNING)
        table_cell(table, title or "—", i, 2)
        table_cell(table, f"${safe_float(amt):.2f}", i, 3, color=C_DANGER, bold=True)
        table_cell(table, notes or "—", i, 4, color=C_MUTED)

        bf = CTkFrame(table, fg_color="transparent")
        bf.grid(row=i + 2, column=5, padx=8, pady=5, sticky="w")

        _ghost_btn(
            bf,
            "Edit",
            lambda id=eid: edit_expense_popup(id, table),
            width=55,
            height=28
        ).pack(side="left", padx=2)

def _expense_form(parent):
    form = CTkFrame(parent, fg_color="transparent")
    form.pack(fill="both", expand=True, padx=10, pady=10)

    # Category
    CTkLabel(form, text="Category").grid(row=0, column=0, sticky="w", pady=6)
    cat_box = CTkComboBox(form, values=EXPENSE_CATS, width=220)
    cat_box.grid(row=0, column=1, pady=6, padx=10)

    # Title
    CTkLabel(form, text="Title").grid(row=1, column=0, sticky="w", pady=6)
    desc_e = CTkEntry(form, width=220)
    desc_e.grid(row=1, column=1, pady=6, padx=10)

    # Amount
    CTkLabel(form, text="Amount").grid(row=2, column=0, sticky="w", pady=6)
    amt_e = CTkEntry(form, width=220)
    amt_e.grid(row=2, column=1, pady=6, padx=10)

    # Date
    CTkLabel(form, text="Date (YYYY-MM-DD)").grid(row=3, column=0, sticky="w", pady=6)
    date_e = CTkEntry(form, width=220)
    date_e.grid(row=3, column=1, pady=6, padx=10)

    return cat_box, desc_e, amt_e, date_e

def add_expense_popup():
    overlay, panel, err = overlay_modal(app, "Add Expense")

    cb, de, ae, dte, _ = _expense_form(panel)  # ignore old switch
    cb.set(EXPENSE_CATS[0])
    dte.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def save():
        cat = cb.get().strip()
        title = de.get().strip()
        amt = safe_float(ae.get().strip(), None)
        dt = dte.get().strip()

        if not cat:
            err.configure(text="Select a category.")
            return

        if not title:
            err.configure(text="Enter a title.")
            return

        if amt is None or amt <= 0:
            err.configure(text="Enter a valid amount.")
            return

        try:
            cursor.execute(
                "INSERT INTO Expenses (Title, Amount, Category, DateTime, Notes) VALUES (?, ?, ?, ?, ?)",
                (title, amt, cat, dt, "")
            )
            conn.commit()
            overlay.destroy()
            refresh_financials_page()

        except Exception as e:
            err.configure(text=str(e))

    modal_buttons(panel, overlay, save, save_text="Add Expense")

def edit_expense_popup(eid, table=None):
    overlay, panel, err = overlay_modal(app, "Edit Expense")

    try:
        cursor.execute(
            "SELECT Category, Title, Amount, DateTime, Notes FROM Expenses WHERE ExpenseID=?",
            (eid,)
        )
        ex = cursor.fetchone()
    except:
        err.configure(text="Expense not found.")
        return

    if not ex:
        err.configure(text="Expense not found.")
        return

    # form (no recurring switch anymore)
    cb, de, ae, dte = _expense_form(panel)

    # populate fields
    cb.set(ex[0] or EXPENSE_CATS[0])
    de.insert(0, ex[1] or "")
    ae.insert(0, str(ex[2] or ""))
    dte.insert(0, format_date(ex[3]))

    def save():
        cat = cb.get().strip()
        title = de.get().strip()
        amt = safe_float(ae.get().strip(), None)
        dt = dte.get().strip()

        if not cat:
            err.configure(text="Select a category.")
            return

        if not title:
            err.configure(text="Enter a title.")
            return

        if amt is None or amt <= 0:
            err.configure(text="Enter a valid amount.")
            return

        try:
            cursor.execute(
                "UPDATE Expenses SET Category=?, Title=?, Amount=?, DateTime=?, Notes=? WHERE ExpenseID=?",
                (cat, title, amt, dt, "", eid)
            )
            conn.commit()

            overlay.destroy()
            refresh_financials_page()

        except Exception as e:
            err.configure(text=str(e))

    def delete():
        try:
            cursor.execute("DELETE FROM Expenses WHERE ExpenseID=?", (eid,))
            conn.commit()
        except Exception as e:
            err.configure(text=str(e))
            return

        overlay.destroy()
        refresh_financials_page()

    modal_buttons(panel, overlay, save, delete, "Save Changes", "Delete")

# ═══════════════════════════════════════════════════════════════
#  TAB SWITCHING
# ═══════════════════════════════════════════════════════════════

def show_content(tab):
    for f in ALL_FRAMES: f.grid_remove()
    _set_active_tab(tab)
    if tab=="Dashboard":
        dashboard_frame.grid(row=0,column=0,sticky="nsew"); create_dashboard()
    elif tab=="Hairdressers":
        hairdresser_frame.grid(row=0,column=0,sticky="nsew"); refresh_hairdresser_page()
    elif tab=="Clients":
        clients_frame.grid(row=0,column=0,sticky="nsew"); refresh_clients_page()
    elif tab=="Products":
        products_frame.grid(row=0,column=0,sticky="nsew"); refresh_products_page()
    elif tab=="Schedule":
        hairdresser_bookings_frame.grid(row=0,column=0,sticky="nsew"); refresh_hairdresser_bookings_page()
    elif tab=="Orders":
        orders_frame.grid(row=0,column=0,sticky="nsew"); refresh_orders_page()
    elif tab=="Financials":
        financials_frame.grid(row=0,column=0,sticky="nsew"); refresh_financials_page()

# ═══════════════════════════════════════════════════════════════
#  START
# ═══════════════════════════════════════════════════════════════

show_content("Dashboard")
app.mainloop()

