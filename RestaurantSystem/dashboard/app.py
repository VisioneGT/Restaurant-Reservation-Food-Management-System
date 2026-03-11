"""
dashboard/app.py
────────────────
Ekhaya Restaurant Management System
Dark red and gold theme — 5 page Dash app

Pages:
  /              → Home
  /reservations  → View, add, update, cancel reservations
  /tables        → Table availability management
  /menu          → Menu and inventory management
  /reports       → Business reporting and analytics

Run: python app.py
Open: http://127.0.0.1:8050
"""

import os, sys, sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context, no_update, ALL
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "../database/restaurant.db")

# ── AUTO SETUP DB IF MISSING ──────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    sys.path.append(os.path.join(BASE_DIR, "../database"))
    from setup_db import setup
    setup()

# ── DB HELPERS ────────────────────────────────────────────────────────────

def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    # pandas reads INTEGER cols with any NULL as float64 — cast back
    for col in df.columns:
        if col.endswith("_id") or col in ("reservation_id","table_id","party_size","item_id","capacity"):
            if df[col].dtype == "float64":
                df[col] = df[col].apply(lambda x: int(x) if pd.notna(x) and x != 0 else x)
    return df

def execute(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    c    = conn.cursor()
    c.execute(sql, params)
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id

# ── THEME ─────────────────────────────────────────────────────────────────

BG       = "#0d0d0d"
BG_CARD  = "#1a0a0a"
BG_CHART = "#1f1010"
CRIMSON  = "#8B0000"
GOLD     = "#D4AF37"
GOLD_LT  = "#F0D060"
TEXT     = "#F5F0E8"
MUTED    = "#9A8A7A"
SUCCESS  = "#2ecc71"
DANGER   = "#e74c3c"
RULE     = "#3a1a1a"

CARD = {
    "background": BG_CARD, "borderRadius": "12px",
    "padding": "18px 22px", "textAlign": "center",
    "flex": "1", "margin": "6px", "minWidth": "130px",
    "border": f"1px solid {RULE}",
    "boxShadow": f"0 4px 16px rgba(139,0,0,0.3)"
}
CHART_CARD = {
    "background": BG_CHART, "borderRadius": "12px",
    "padding": "12px", "flex": "1",
    "minWidth": "320px", "margin": "8px",
    "border": f"1px solid {RULE}"
}
INPUT_STYLE = {
    "background": "#2a1010", "color": TEXT,
    "border": f"1px solid {CRIMSON}", "borderRadius": "6px",
    "padding": "8px 12px", "width": "100%",
    "fontSize": "13px", "marginBottom": "10px",
    "boxSizing": "border-box"
}
BTN = {
    "background": CRIMSON, "color": TEXT,
    "border": "none", "borderRadius": "6px",
    "padding": "10px 22px", "cursor": "pointer",
    "fontSize": "13px", "fontWeight": "600",
    "marginRight": "8px"
}
BTN_GOLD = {**BTN, "background": GOLD, "color": "#1a0a0a"}
BTN_GREY = {**BTN, "background": "#333", "color": TEXT}
NAV_LINK = {
    "color": MUTED, "textDecoration": "none",
    "padding": "8px 14px", "borderRadius": "6px",
    "fontSize": "13px", "fontWeight": "500"
}
NAV_ACTIVE = {**NAV_LINK, "color": "#1a0a0a", "background": GOLD, "fontWeight": "700"}
TH_STYLE = {
    "padding": "10px 14px", "color": GOLD,
    "fontSize": "11px", "textTransform": "uppercase",
    "borderBottom": f"2px solid {CRIMSON}",
    "textAlign": "left", "whiteSpace": "nowrap"
}
TD_STYLE = {
    "padding": "9px 14px", "color": TEXT,
    "fontSize": "13px", "borderBottom": f"1px solid {RULE}",
    "verticalAlign": "middle"
}

STATUS_COLORS = {
    "Completed": SUCCESS, "Confirmed": GOLD,
    "Pending": "#f39c12", "Cancelled": DANGER
}

# ── COMPONENTS ────────────────────────────────────────────────────────────

def navbar(current):
    pages = [
        ("/",             "🏠 Home"),
        ("/reservations", "📅 Reservations"),
        ("/tables",       "🪑 Tables"),
        ("/menu",         "🍽️ Menu"),
        ("/reports",      "📊 Reports"),
    ]
    links = [
        html.A(label, href=path,
               style=NAV_ACTIVE if current == path else NAV_LINK)
        for path, label in pages
    ]
    return html.Div(style={
        "background": BG_CARD,
        "padding": "0 28px",
        "display": "flex", "alignItems": "center",
        "justifyContent": "space-between",
        "height": "58px",
        "boxShadow": f"0 2px 16px rgba(139,0,0,0.5)",
        "position": "sticky", "top": "0", "zIndex": "1000",
        "borderBottom": f"2px solid {CRIMSON}"
    }, children=[
        html.Div([
            html.Span("🍷", style={"fontSize": "22px", "marginRight": "10px"}),
            html.Span("Ekhaya Restaurant",
                      style={"color": GOLD, "fontWeight": "800",
                             "fontSize": "17px", "letterSpacing": "1px"}),
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div(links, style={"display": "flex", "gap": "4px", "alignItems": "center"}),
    ])


def kpi(label, value, color=GOLD):
    return html.Div([
        html.P(label, style={"color": MUTED, "margin": "0 0 4px 0",
               "fontSize": "10px", "textTransform": "uppercase",
               "letterSpacing": "1px"}),
        html.H3(value, style={"color": color, "margin": "0",
                "fontSize": "20px", "fontWeight": "700"}),
    ], style=CARD)


def section_title(text):
    return html.H2(text, style={
        "color": GOLD, "margin": "0 0 4px 0",
        "fontSize": "20px", "fontWeight": "700",
        "borderBottom": f"2px solid {CRIMSON}",
        "paddingBottom": "8px", "marginBottom": "16px"
    })


def status_badge(status):
    color = STATUS_COLORS.get(status, MUTED)
    return html.Span(status, style={
        "background": color + "22", "color": color,
        "padding": "3px 10px", "borderRadius": "12px",
        "fontSize": "11px", "fontWeight": "600",
        "border": f"1px solid {color}"
    })


def form_label(text):
    return html.Label(text, style={
        "color": MUTED, "fontSize": "11px",
        "textTransform": "uppercase", "letterSpacing": "1px",
        "marginBottom": "4px", "display": "block"
    })


# ── PAGE: HOME ────────────────────────────────────────────────────────────

def page_home():
    res   = query("SELECT * FROM reservations")
    today = date.today().isoformat()

    total_res    = len(res)
    today_res    = len(res[res["date"] == today])
    confirmed    = len(res[res["status"].isin(["Confirmed", "Pending"])])
    cancelled    = len(res[res["status"] == "Cancelled"])
    cancel_rate  = round(cancelled / total_res * 100, 1) if total_res > 0 else 0

    menu  = query("SELECT * FROM menu")
    inv   = query("SELECT * FROM inventory WHERE quantity_in_stock <= minimum_stock")
    tables= query("SELECT * FROM tables")
    avail = len(tables[tables["status"] == "Available"])

    features = [
        ("📅", "Reservations", "Book, update and cancel table reservations with real-time conflict prevention.", "/reservations"),
        ("🪑", "Table Management", "Track availability of all 10 tables across indoor, outdoor and private dining.", "/tables"),
        ("🍽️", "Menu & Inventory", "Manage the full menu and monitor ingredient stock levels.", "/menu"),
        ("📊", "Reports", "Analyse busiest days, top dishes, revenue trends and cancellation rates.", "/reports"),
    ]

    feat_cards = [html.A(href=link, style={"textDecoration": "none"}, children=[
        html.Div([
            html.Div(icon, style={"fontSize": "28px", "marginBottom": "10px"}),
            html.H3(title, style={"color": GOLD, "margin": "0 0 6px 0", "fontSize": "14px"}),
            html.P(desc, style={"color": MUTED, "margin": "0", "fontSize": "12px", "lineHeight": "1.6"}),
        ], style={**CHART_CARD, "minWidth": "180px", "padding": "20px",
                  "cursor": "pointer", "transition": "border-color 0.2s",
                  "border": f"1px solid {CRIMSON}"})
    ]) for icon, title, desc, link in features]

    return html.Div([
        navbar("/"),
        html.Div(style={"padding": "40px 28px", "maxWidth": "900px", "margin": "0 auto"}, children=[
            html.Div(style={"textAlign": "center", "marginBottom": "48px"}, children=[
                html.Div("🍷", style={"fontSize": "64px"}),
                html.H1("Ekhaya Restaurant",
                        style={"color": GOLD, "fontSize": "32px",
                               "margin": "12px 0 4px 0", "fontWeight": "800",
                               "letterSpacing": "2px"}),
                html.P("Management System",
                       style={"color": CRIMSON, "fontSize": "14px",
                              "letterSpacing": "4px", "margin": "0 0 8px 0",
                              "textTransform": "uppercase"}),
                html.P("Johannesburg, South Africa",
                       style={"color": MUTED, "fontSize": "13px", "margin": "0"}),
            ]),

            html.Div(style={"display": "flex", "flexWrap": "wrap", "marginBottom": "32px"}, children=[
                kpi("Total Reservations", str(total_res)),
                kpi("Today's Bookings",   str(today_res)),
                kpi("Upcoming",           str(confirmed), GOLD_LT),
                kpi("Tables Available",   f"{avail}/10", SUCCESS if avail > 3 else DANGER),
                kpi("Menu Items",         str(len(menu))),
                kpi("Low Stock Alerts",   str(len(inv)), DANGER if len(inv) > 0 else SUCCESS),
                kpi("Cancellation Rate",  f"{cancel_rate}%", DANGER if cancel_rate > 15 else SUCCESS),
            ]),

            html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=feat_cards),
        ])
    ])


# ── PAGE: RESERVATIONS ────────────────────────────────────────────────────

def build_reservations_table(df):
    if df.empty:
        return html.P("No reservations found.", style={"color": MUTED, "padding": "20px"})
    df = df.copy()
    rows = []
    for _, r in df.iterrows():
        rows.append(html.Tr([
            html.Td(str(int(r["reservation_id"])) if pd.notna(r["reservation_id"]) else "—", style={**TD_STYLE, "color": MUTED}),
            html.Td(r["customer_name"],       style={**TD_STYLE, "fontWeight": "600"}),
            html.Td(r["phone"],               style=TD_STYLE),
            html.Td(r["date"],                style=TD_STYLE),
            html.Td(r["time"],                style=TD_STYLE),
            html.Td(str(r["party_size"]),     style={**TD_STYLE, "textAlign": "center"}),
            html.Td(f"T0{r['table_id']}" if r["table_id"] else "—", style=TD_STYLE),
            html.Td(status_badge(r["status"]), style={**TD_STYLE}),
            html.Td(r["special_requests"] if r["special_requests"] else "—",
                    style={**TD_STYLE, "color": MUTED, "fontSize": "12px"}),
        ], style={"borderBottom": f"1px solid {RULE}"}))
    return html.Table(style={"width": "100%", "borderCollapse": "collapse"}, children=[
        html.Thead(html.Tr([
            html.Th("ID",       style=TH_STYLE),
            html.Th("Guest",    style=TH_STYLE),
            html.Th("Phone",    style=TH_STYLE),
            html.Th("Date",     style=TH_STYLE),
            html.Th("Time",     style=TH_STYLE),
            html.Th("Party",    style={**TH_STYLE, "textAlign": "center"}),
            html.Th("Table",    style=TH_STYLE),
            html.Th("Status",   style=TH_STYLE),
            html.Th("Requests", style=TH_STYLE),
        ])),
        html.Tbody(rows)
    ])


def page_reservations():
    res    = query("SELECT * FROM reservations ORDER BY date DESC, time DESC")
    tables = query("SELECT * FROM tables ORDER BY table_id")
    table_opts = [{"label": f"Table {r['table_number']} ({r['capacity']} seats — {r['location']})",
                   "value": r["table_id"]} for _, r in tables.iterrows()]

    status_opts = [{"label": s, "value": s}
                   for s in ["All", "Pending", "Confirmed", "Completed", "Cancelled"]]
    filter_opts = [{"label": s, "value": s}
                   for s in ["All", "Pending", "Confirmed", "Completed", "Cancelled"]]

    total      = len(res)
    upcoming   = len(res[res["status"].isin(["Pending", "Confirmed"])])
    completed  = len(res[res["status"] == "Completed"])
    cancelled  = len(res[res["status"] == "Cancelled"])

    return html.Div([
        navbar("/reservations"),
        html.Div(style={"padding": "24px 28px", "background": BG, "minHeight": "100vh"}, children=[
            section_title("📅 Reservations"),

            html.Div(style={"display": "flex", "flexWrap": "wrap", "marginBottom": "20px"}, children=[
                kpi("Total Reservations", str(total)),
                kpi("Upcoming",           str(upcoming),  GOLD_LT),
                kpi("Completed",          str(completed), SUCCESS),
                kpi("Cancelled",          str(cancelled), DANGER),
            ]),

            # ── Add Reservation form ─────────────────────────────────
            html.Div(style={**CHART_CARD, "marginBottom": "20px", "minWidth": "100%"}, children=[
                html.H3("➕ New Reservation",
                        style={"color": GOLD, "margin": "0 0 16px 0", "fontSize": "15px"}),
                html.Div(style={"display": "flex", "flexWrap": "wrap", "gap": "16px"}, children=[
                    html.Div(style={"flex": "1", "minWidth": "160px"}, children=[
                        form_label("Guest Name"),
                        dcc.Input(id="new-name", placeholder="Full name",
                                  style=INPUT_STYLE, debounce=True),
                    ]),
                    html.Div(style={"flex": "1", "minWidth": "140px"}, children=[
                        form_label("Phone Number"),
                        dcc.Input(id="new-phone", placeholder="e.g. 0821234567",
                                  style=INPUT_STYLE, debounce=True),
                    ]),
                    html.Div(style={"flex": "1", "minWidth": "140px"}, children=[
                        form_label("Email (optional)"),
                        dcc.Input(id="new-email", placeholder="email@example.com",
                                  style=INPUT_STYLE, debounce=True),
                    ]),
                    html.Div(style={"flex": "1", "minWidth": "160px"}, children=[
                        form_label("Date"),
                        dcc.DatePickerSingle(
                            id="new-date",
                            date=date.today().isoformat(),
                            display_format="YYYY-MM-DD",
                            style={"width": "100%"},
                        ),
                    ]),
                    html.Div(style={"flex": "1", "minWidth": "120px"}, children=[
                        form_label("Time"),
                        dcc.Dropdown(id="new-time",
                            options=[{"label": t, "value": t} for t in
                                     ["12:00","12:30","13:00","13:30","14:00",
                                      "17:00","17:30","18:00","18:30","19:00",
                                      "19:30","20:00","20:30","21:00"]],
                            value="19:00",
                            style={"fontSize": "13px"},
                            className="dark-dropdown"),
                    ]),
                    html.Div(style={"flex": "1", "minWidth": "100px"}, children=[
                        form_label("Party Size"),
                        dcc.Input(id="new-party", type="number",
                                  min=1, max=12, value=2,
                                  style=INPUT_STYLE),
                    ]),
                    html.Div(style={"flex": "1", "minWidth": "180px"}, children=[
                        form_label("Table"),
                        dcc.Dropdown(id="new-table", options=table_opts,
                                     placeholder="Select table",
                                     style={"fontSize": "13px"},
                                     className="dark-dropdown"),
                    ]),
                    html.Div(style={"flex": "2", "minWidth": "200px"}, children=[
                        form_label("Special Requests"),
                        dcc.Input(id="new-requests",
                                  placeholder="Allergies, birthday, high chair...",
                                  style=INPUT_STYLE, debounce=True),
                    ]),
                ]),
                html.Div(style={"marginTop": "12px", "display": "flex", "gap": "8px",
                                "alignItems": "center"}, children=[
                    html.Button("Book Reservation", id="btn-add-res",
                                style=BTN_GOLD, n_clicks=0),
                    html.Div(id="res-add-msg",
                             style={"fontSize": "13px", "color": SUCCESS}),
                ]),
            ]),

            # ── Update / Cancel form ─────────────────────────────────
            html.Div(style={**CHART_CARD, "marginBottom": "20px", "minWidth": "100%"}, children=[
                html.H3("✏️ Update / Cancel Reservation",
                        style={"color": GOLD, "margin": "0 0 16px 0", "fontSize": "15px"}),
                html.Div(style={"display": "flex", "flexWrap": "wrap", "gap": "16px",
                                "alignItems": "flex-end"}, children=[
                    html.Div(style={"flex": "1", "minWidth": "120px"}, children=[
                        form_label("Reservation ID"),
                        dcc.Input(id="upd-id", type="number",
                                  placeholder="Enter ID", style=INPUT_STYLE),
                    ]),
                    html.Div(style={"flex": "1", "minWidth": "140px"}, children=[
                        form_label("New Status"),
                        dcc.Dropdown(id="upd-status",
                            options=[{"label": s, "value": s}
                                     for s in ["Confirmed","Completed","Cancelled","Pending"]],
                            placeholder="Select status",
                            style={"fontSize": "13px"},
                            className="dark-dropdown"),
                    ]),
                    html.Div(style={"display": "flex", "gap": "8px",
                                   "alignItems": "flex-end", "paddingBottom": "10px"}, children=[
                        html.Button("Update Status", id="btn-update-res",
                                    style=BTN, n_clicks=0),
                        html.Div(id="res-upd-msg",
                                 style={"fontSize": "13px", "color": SUCCESS,
                                        "lineHeight": "38px"}),
                    ]),
                ]),
            ]),

            # ── Filter + table ────────────────────────────────────────
            html.Div(style={**CHART_CARD, "minWidth": "100%"}, children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between",
                                "alignItems": "center", "marginBottom": "12px"}, children=[
                    html.H3("All Reservations",
                            style={"color": GOLD, "margin": "0", "fontSize": "15px"}),
                    html.Div(style={"display": "flex", "gap": "10px",
                                   "alignItems": "center"}, children=[
                        html.Label("Filter:", style={"color": MUTED, "fontSize": "12px"}),
                        dcc.Dropdown(id="filter-status",
                            options=filter_opts, value="All",
                            style={"width": "150px", "fontSize": "13px"},
                            className="dark-dropdown",
                            clearable=False),
                    ]),
                ]),
                html.Div(id="reservations-table",
                         style={"overflowX": "auto"},
                         children=[build_reservations_table(res)]),
            ]),
        ])
    ])


# ── PAGE: TABLES ──────────────────────────────────────────────────────────

def page_tables():
    tables = query("SELECT * FROM tables ORDER BY table_id")
    today  = date.today().isoformat()
    booked_today = query(
        "SELECT DISTINCT table_id FROM reservations WHERE date=? AND status IN ('Confirmed','Pending')",
        (today,)
    )["table_id"].tolist()

    cards = []
    for _, t in tables.iterrows():
        is_booked = t["table_id"] in booked_today
        effective = "Occupied" if is_booked else t["status"]
        color     = DANGER if effective == "Occupied" else (
                    SUCCESS if effective == "Available" else GOLD)
        icon      = "🔴" if effective == "Occupied" else (
                    "🟢" if effective == "Available" else "🟡")

        cards.append(html.Div([
            html.Div(style={"display": "flex", "justifyContent": "space-between",
                           "alignItems": "flex-start"}, children=[
                html.Div([
                    html.P(t["table_number"],
                           style={"color": GOLD, "fontWeight": "800",
                                  "fontSize": "18px", "margin": "0"}),
                    html.P(t["location"],
                           style={"color": MUTED, "fontSize": "11px", "margin": "2px 0 0 0"}),
                ]),
                html.Span(icon + " " + effective,
                          style={"color": color, "fontSize": "11px",
                                 "fontWeight": "600", "background": color + "22",
                                 "padding": "3px 10px", "borderRadius": "12px",
                                 "border": f"1px solid {color}"}),
            ]),
            html.Div(style={"marginTop": "12px", "display": "flex",
                           "alignItems": "center", "gap": "8px"}, children=[
                html.Span("👥", style={"fontSize": "16px"}),
                html.Span(f"{t['capacity']} guests",
                          style={"color": TEXT, "fontSize": "14px", "fontWeight": "600"}),
            ]),
            html.Div(style={"marginTop": "12px", "display": "flex",
                                "flexWrap": "wrap", "gap": "6px"}, children=[
                html.Button("✅ Available", id={"type": "tbl-avail", "index": t["table_id"]},
                            style={**BTN_GREY, "fontSize": "11px", "padding": "6px 10px",
                                   "flex": "1", "minWidth": "80px"},
                            n_clicks=0),
                html.Button("🔴 Reserved", id={"type": "tbl-reserved", "index": t["table_id"]},
                            style={**BTN, "fontSize": "11px", "padding": "6px 10px",
                                   "flex": "1", "minWidth": "80px"},
                            n_clicks=0),
                html.Button("🔧 Maintenance", id={"type": "tbl-maint", "index": t["table_id"]},
                            style={**BTN_GREY, "fontSize": "11px", "padding": "6px 10px",
                                   "background": "#5a3a00", "flex": "1", "minWidth": "80px"},
                            n_clicks=0),
            ]),
        ], style={
            **CHART_CARD,
            "minWidth": "200px", "maxWidth": "260px",
            "flex": "1",
            "padding": "16px",
            "border": f"2px solid {color}",
        }))

    loc_counts  = tables.groupby("location").size().reset_index(name="count")
    stat_counts = tables["status"].value_counts().reset_index()
    stat_counts.columns = ["status", "count"]

    fig_loc = px.pie(loc_counts, values="count", names="location",
                     title="Tables by Location",
                     color_discrete_sequence=[CRIMSON, GOLD, "#8a4a00", "#4a0000"],
                     template="plotly_dark")
    fig_loc.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART)

    avail_count = len(tables[tables["status"] == "Available"])
    occupied    = len(booked_today)
    other       = len(tables) - avail_count - occupied

    fig_avail = go.Figure(go.Pie(
        labels=["Available", "Occupied Today", "Other"],
        values=[max(0, avail_count - occupied), occupied, other],
        marker_colors=[SUCCESS, DANGER, GOLD],
        hole=0.5
    ))
    fig_avail.update_layout(
        title="Today's Occupancy",
        paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART,
        font=dict(color=TEXT), template="plotly_dark"
    )

    return html.Div([
        navbar("/tables"),
        html.Div(id="tables-update-msg"),
        html.Div(style={"padding": "24px 28px", "background": BG, "minHeight": "100vh"}, children=[
            section_title("🪑 Table Management"),
            html.P(f"Today: {today}  •  {avail_count} tables available  •  {occupied} reserved today",
                   style={"color": MUTED, "margin": "-10px 0 20px 0", "fontSize": "12px"}),

            html.Div(style={"display": "flex", "flexWrap": "wrap", "marginBottom": "20px"}, children=[
                kpi("Total Tables",     "10"),
                kpi("Available",        str(avail_count),            SUCCESS),
                kpi("Reserved Today",   str(occupied),               DANGER if occupied > 5 else GOLD),
                kpi("Total Capacity",   str(tables["capacity"].sum())),
            ]),

            html.Div(style={"display": "flex", "flexWrap": "wrap",
                                "gap": "12px", "marginBottom": "20px"},
                     children=cards),

            html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=[
                html.Div(dcc.Graph(figure=fig_avail, config={"displayModeBar": False}),
                         style={**CHART_CARD, "flex": "1"}),
                html.Div(dcc.Graph(figure=fig_loc, config={"displayModeBar": False}),
                         style={**CHART_CARD, "flex": "1"}),
            ]),
        ])
    ])


# ── PAGE: MENU ────────────────────────────────────────────────────────────

def page_menu():
    menu = query("SELECT * FROM menu ORDER BY category, name")
    inv  = query("SELECT * FROM inventory ORDER BY ingredient")

    inv["low_stock"]   = inv["quantity_in_stock"] <= inv["minimum_stock"]
    inv["stock_pct"]   = (inv["quantity_in_stock"] / (inv["minimum_stock"] * 3) * 100).clip(0, 100).round(0)
    low_stock_count    = inv["low_stock"].sum()

    # Category breakdown chart
    cat_counts = menu.groupby("category").agg(
        count=("name", "count"),
        avg_price=("price", "mean")
    ).reset_index()

    fig_cat = px.bar(cat_counts, x="category", y="count",
                     title="Menu Items by Category",
                     color="avg_price",
                     color_continuous_scale=[[0, CRIMSON], [1, GOLD]],
                     labels={"count": "Number of Items", "category": "",
                             "avg_price": "Avg Price (R)"},
                     template="plotly_dark")
    fig_cat.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART)

    # Price distribution
    fig_price = px.box(menu, x="category", y="price",
                       title="Price Distribution by Category",
                       color="category",
                       color_discrete_sequence=[CRIMSON, GOLD, "#8a4a00", "#c06000"],
                       labels={"price": "Price (R)", "category": ""},
                       template="plotly_dark")
    fig_price.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART,
                             showlegend=False)

    # Menu table
    menu_rows = []
    for _, r in menu.iterrows():
        tags = []
        if r["is_vegetarian"]: tags.append(html.Span("🌿 Veg", style={"background": "#1a3a1a", "color": SUCCESS, "padding": "2px 6px", "borderRadius": "4px", "fontSize": "10px", "marginRight": "4px"}))
        if r["is_halaal"]:     tags.append(html.Span("☪️ Halaal", style={"background": "#1a1a3a", "color": "#7fb3ff", "padding": "2px 6px", "borderRadius": "4px", "fontSize": "10px", "marginRight": "4px"}))
        avail_badge = html.Span(
            "✅ Available" if r["is_available"] else "❌ Unavailable",
            style={"color": SUCCESS if r["is_available"] else DANGER,
                   "fontSize": "11px", "fontWeight": "600"}
        )
        menu_rows.append(html.Tr([
            html.Td(r["name"],          style={**TD_STYLE, "fontWeight": "600"}),
            html.Td(r["category"],      style=TD_STYLE),
            html.Td(f"R {r['price']:.0f}", style={**TD_STYLE, "color": GOLD, "fontWeight": "700"}),
            html.Td(r["description"],   style={**TD_STYLE, "color": MUTED, "fontSize": "11px"}),
            html.Td(html.Div(tags),     style=TD_STYLE),
            html.Td(f"{r['prep_time_mins']} min", style={**TD_STYLE, "color": MUTED}),
            html.Td(avail_badge,        style=TD_STYLE),
        ]))

    menu_table = html.Table(style={"width": "100%", "borderCollapse": "collapse"}, children=[
        html.Thead(html.Tr([
            html.Th("Item",        style=TH_STYLE),
            html.Th("Category",    style=TH_STYLE),
            html.Th("Price",       style=TH_STYLE),
            html.Th("Description", style=TH_STYLE),
            html.Th("Dietary",     style=TH_STYLE),
            html.Th("Prep Time",   style=TH_STYLE),
            html.Th("Status",      style=TH_STYLE),
        ])),
        html.Tbody(menu_rows)
    ])

    # Inventory table
    inv_rows = []
    for _, r in inv.iterrows():
        bar_color = DANGER if r["low_stock"] else (
                    GOLD   if r["stock_pct"] < 60 else SUCCESS)
        inv_rows.append(html.Tr([
            html.Td(r["ingredient"],   style={**TD_STYLE, "fontWeight": "600"}),
            html.Td(f"{r['quantity_in_stock']} {r['unit']}",
                    style={**TD_STYLE, "color": DANGER if r["low_stock"] else TEXT,
                           "fontWeight": "700" if r["low_stock"] else "400"}),
            html.Td(f"{r['minimum_stock']} {r['unit']}", style={**TD_STYLE, "color": MUTED}),
            html.Td(html.Div([
                html.Div(style={"background": "#3a1a1a", "borderRadius": "4px",
                                "height": "8px", "width": "100px",
                                "overflow": "hidden"}, children=[
                    html.Div(style={"background": bar_color, "height": "100%",
                                   "width": f"{r['stock_pct']}%",
                                   "borderRadius": "4px"})
                ])
            ]), style=TD_STYLE),
            html.Td(f"R {r['unit_cost']:.2f}", style={**TD_STYLE, "color": MUTED}),
            html.Td(r["supplier"],     style={**TD_STYLE, "color": MUTED, "fontSize": "11px"}),
            html.Td(r["last_restocked"], style={**TD_STYLE, "color": MUTED, "fontSize": "11px"}),
            html.Td(
                html.Span("⚠️ LOW", style={"color": DANGER, "fontWeight": "700", "fontSize": "11px"})
                if r["low_stock"] else
                html.Span("✅ OK",  style={"color": SUCCESS, "fontSize": "11px"}),
                style=TD_STYLE
            ),
        ]))

    inv_table = html.Table(style={"width": "100%", "borderCollapse": "collapse"}, children=[
        html.Thead(html.Tr([
            html.Th("Ingredient",   style=TH_STYLE),
            html.Th("In Stock",     style=TH_STYLE),
            html.Th("Min Stock",    style=TH_STYLE),
            html.Th("Level",        style=TH_STYLE),
            html.Th("Unit Cost",    style=TH_STYLE),
            html.Th("Supplier",     style=TH_STYLE),
            html.Th("Restocked",    style=TH_STYLE),
            html.Th("Status",       style=TH_STYLE),
        ])),
        html.Tbody(inv_rows)
    ])

    return html.Div([
        navbar("/menu"),
        html.Div(style={"padding": "24px 28px", "background": BG, "minHeight": "100vh"}, children=[
            section_title("🍽️ Menu & Inventory"),

            html.Div(style={"display": "flex", "flexWrap": "wrap", "marginBottom": "20px"}, children=[
                kpi("Total Menu Items",   str(len(menu))),
                kpi("Available Items",    str(menu["is_available"].sum()), SUCCESS),
                kpi("Vegetarian Options", str(menu["is_vegetarian"].sum()), SUCCESS),
                kpi("Halaal Options",     str(menu["is_halaal"].sum()), GOLD),
                kpi("Low Stock Alerts",   str(low_stock_count), DANGER if low_stock_count > 0 else SUCCESS),
                kpi("Ingredients Tracked",str(len(inv))),
            ]),

            html.Div(style={"display": "flex", "flexWrap": "wrap", "marginBottom": "16px"}, children=[
                html.Div(dcc.Graph(figure=fig_cat, config={"displayModeBar": False}),
                         style={**CHART_CARD, "flex": "1"}),
                html.Div(dcc.Graph(figure=fig_price, config={"displayModeBar": False}),
                         style={**CHART_CARD, "flex": "1"}),
            ]),

            html.Div(style={**CHART_CARD, "minWidth": "100%", "marginBottom": "16px"}, children=[
                html.H3("Full Menu", style={"color": GOLD, "margin": "0 0 16px 0", "fontSize": "15px"}),
                html.Div(menu_table, style={"overflowX": "auto"}),
            ]),

            html.Div(style={**CHART_CARD, "minWidth": "100%"}, children=[
                html.H3("Inventory Management",
                        style={"color": GOLD, "margin": "0 0 4px 0", "fontSize": "15px"}),
                html.P(f"{low_stock_count} ingredient(s) at or below minimum stock level",
                       style={"color": DANGER if low_stock_count > 0 else MUTED,
                              "fontSize": "12px", "margin": "0 0 12px 0"}),
                html.Div(inv_table, style={"overflowX": "auto"}),
            ]),
        ])
    ])


# ── PAGE: REPORTS ─────────────────────────────────────────────────────────

def page_reports():
    res    = query("SELECT * FROM reservations")
    orders = query("SELECT * FROM orders")

    res["date"]        = pd.to_datetime(res["date"])
    res["month_name"]  = res["date"].dt.month_name()
    res["day_name"]    = res["date"].dt.day_name()
    res["month"]       = res["date"].dt.month
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["month_name"] = orders["order_date"].dt.month_name()
    orders["revenue"]    = orders["quantity"] * orders["unit_price"]

    # KPIs
    total_res      = len(res)
    completed      = len(res[res["status"] == "Completed"])
    cancel_rate    = round(len(res[res["status"] == "Cancelled"]) / total_res * 100, 1)
    total_revenue  = orders["revenue"].sum()
    avg_party      = round(res["party_size"].mean(), 1)
    top_day        = res["day_name"].value_counts().idxmax()

    # Reservations by month
    month_order = ["January", "February", "March"]
    monthly_res = res.groupby("month_name").size().reset_index(name="count")
    monthly_res["month_name"] = pd.Categorical(monthly_res["month_name"],
                                               categories=month_order, ordered=True)
    monthly_res = monthly_res.sort_values("month_name")

    fig_monthly = px.bar(monthly_res, x="month_name", y="count",
                         title="Reservations by Month",
                         labels={"count": "Reservations", "month_name": "Month"},
                         color="count",
                         color_continuous_scale=[[0, CRIMSON], [1, GOLD]],
                         template="plotly_dark")
    fig_monthly.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART)

    # Busiest days
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_counts = res.groupby("day_name").size().reset_index(name="count")
    day_counts["day_name"] = pd.Categorical(day_counts["day_name"],
                                            categories=day_order, ordered=True)
    day_counts = day_counts.sort_values("day_name")

    fig_days = px.bar(day_counts, x="day_name", y="count",
                      title="Busiest Days of the Week",
                      labels={"count": "Reservations", "day_name": "Day"},
                      color="count",
                      color_continuous_scale=[[0, CRIMSON], [1, GOLD]],
                      template="plotly_dark")
    fig_days.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART)

    # Status breakdown
    status_counts = res["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig_status = px.pie(status_counts, values="count", names="status",
                        title="Reservation Status Breakdown",
                        color_discrete_sequence=[SUCCESS, GOLD, CRIMSON, MUTED],
                        template="plotly_dark")
    fig_status.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART)

    # Top menu items by orders
    top_items = orders.groupby("item_name").agg(
        total_ordered=("quantity", "sum"),
        total_revenue=("revenue", "sum")
    ).reset_index().sort_values("total_ordered", ascending=False).head(10)

    fig_items = px.bar(top_items, x="total_ordered", y="item_name",
                       orientation="h",
                       title="Top 10 Most Ordered Dishes",
                       labels={"total_ordered": "Total Ordered", "item_name": ""},
                       color="total_revenue",
                       color_continuous_scale=[[0, CRIMSON], [1, GOLD]],
                       template="plotly_dark")
    fig_items.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART,
                             yaxis={"categoryorder": "total ascending"})

    # Revenue by category
    cat_rev = orders.groupby("category")["revenue"].sum().reset_index()
    fig_cat_rev = px.pie(cat_rev, values="revenue", names="category",
                         title="Revenue by Menu Category",
                         color_discrete_sequence=[CRIMSON, GOLD, "#8a4a00", "#c06000"],
                         template="plotly_dark")
    fig_cat_rev.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART)

    # Monthly revenue
    monthly_rev = orders.groupby("month_name")["revenue"].sum().reset_index()
    monthly_rev["month_name"] = pd.Categorical(monthly_rev["month_name"],
                                               categories=month_order, ordered=True)
    monthly_rev = monthly_rev.sort_values("month_name")

    fig_rev = px.bar(monthly_rev, x="month_name", y="revenue",
                     title="Monthly Revenue from Orders",
                     labels={"revenue": "Revenue (R)", "month_name": "Month"},
                     color="revenue",
                     color_continuous_scale=[[0, CRIMSON], [1, GOLD]],
                     template="plotly_dark",
                     text="revenue")
    fig_rev.update_traces(texttemplate="R %{text:,.0f}", textposition="outside")
    fig_rev.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART)

    # Party size distribution
    fig_party = px.histogram(res, x="party_size",
                             title="Party Size Distribution",
                             labels={"party_size": "Party Size", "count": "Frequency"},
                             color_discrete_sequence=[CRIMSON],
                             template="plotly_dark",
                             nbins=8)
    fig_party.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_CHART)

    return html.Div([
        navbar("/reports"),
        html.Div(style={"padding": "24px 28px", "background": BG, "minHeight": "100vh"}, children=[
            section_title("📊 Business Reports"),
            html.P("Jan–Mar 2024  •  Based on reservations and order data",
                   style={"color": MUTED, "margin": "-10px 0 20px 0", "fontSize": "12px"}),

            html.Div(style={"display": "flex", "flexWrap": "wrap", "marginBottom": "20px"}, children=[
                kpi("Total Reservations", str(total_res)),
                kpi("Completed",          str(completed),       SUCCESS),
                kpi("Cancellation Rate",  f"{cancel_rate}%",    DANGER if cancel_rate > 15 else SUCCESS),
                kpi("Total Revenue",      f"R {total_revenue:,.0f}", GOLD),
                kpi("Avg Party Size",     str(avg_party)),
                kpi("Busiest Day",        top_day,              GOLD_LT),
            ]),

            html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=[
                html.Div(dcc.Graph(figure=fig_monthly, config={"displayModeBar": False}), style={**CHART_CARD, "flex": "1"}),
                html.Div(dcc.Graph(figure=fig_days,    config={"displayModeBar": False}), style={**CHART_CARD, "flex": "1"}),
            ]),
            html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=[
                html.Div(dcc.Graph(figure=fig_status,  config={"displayModeBar": False}), style={**CHART_CARD, "flex": "1"}),
                html.Div(dcc.Graph(figure=fig_cat_rev, config={"displayModeBar": False}), style={**CHART_CARD, "flex": "1"}),
            ]),
            html.Div(dcc.Graph(figure=fig_items, config={"displayModeBar": False}), style={**CHART_CARD}),
            html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=[
                html.Div(dcc.Graph(figure=fig_rev,   config={"displayModeBar": False}), style={**CHART_CARD, "flex": "1"}),
                html.Div(dcc.Graph(figure=fig_party, config={"displayModeBar": False}), style={**CHART_CARD, "flex": "1"}),
            ]),
        ])
    ])


# ── APP ───────────────────────────────────────────────────────────────────

app = Dash(__name__, suppress_callback_exceptions=True)
app.index_string = '''
<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>Ekhaya Restaurant</title>
{%favicon%}
{%css%}
<style>
  body { margin: 0; background: #0d0d0d; font-family: 'Segoe UI', Arial, sans-serif; }
  .dark-dropdown .Select-control { background: #2a1010 !important; border-color: #8B0000 !important; color: #F5F0E8 !important; }
  .dark-dropdown .Select-menu-outer { background: #1a0a0a !important; border-color: #8B0000 !important; }
  .dark-dropdown .Select-option { background: #1a0a0a !important; color: #F5F0E8 !important; }
  .dark-dropdown .Select-option:hover { background: #3a1010 !important; }
  .dark-dropdown .Select-value-label { color: #F5F0E8 !important; }
  .dark-dropdown .Select-placeholder { color: #9A8A7A !important; }
  .dark-dropdown input { color: #F5F0E8 !important; }
  * { box-sizing: border-box; }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #1a0a0a; }
  ::-webkit-scrollbar-thumb { background: #8B0000; border-radius: 3px; }
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
'''

app.layout = html.Div(
    style={"background": BG, "minHeight": "100vh"},
    children=[
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
    ]
)


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname in ("/", None):   return page_home()
    if pathname == "/reservations": return page_reservations()
    if pathname == "/tables":       return page_tables()
    if pathname == "/menu":         return page_menu()
    if pathname == "/reports":      return page_reports()
    return html.Div([navbar("/"), html.Div([
        html.H1("404", style={"color": GOLD, "fontSize": "64px", "margin": "60px auto 0",
                              "textAlign": "center"}),
        html.P("Page not found.", style={"color": MUTED, "textAlign": "center"}),
        html.Div(html.A("← Home", href="/", style={**NAV_ACTIVE, "display": "inline-block",
                                                    "marginTop": "14px"}),
                 style={"textAlign": "center"}),
    ])])


# ── CALLBACKS ─────────────────────────────────────────────────────────────

@app.callback(
    Output("res-add-msg", "children"),
    Output("res-add-msg", "style"),
    Output("reservations-table", "children", allow_duplicate=True),
    Input("btn-add-res", "n_clicks"),
    State("new-name",     "value"),
    State("new-phone",    "value"),
    State("new-email",    "value"),
    State("new-date",     "date"),
    State("new-time",     "value"),
    State("new-party",    "value"),
    State("new-table",    "value"),
    State("new-requests", "value"),
    prevent_initial_call=True
)
def add_reservation(n, name, phone, email, res_date, res_time,
                    party, table_id, requests):
    if not n: return no_update, no_update, no_update
    if not name or not phone or not res_date or not res_time or not party:
        return "⚠️ Please fill in name, phone, date, time and party size.", \
               {"fontSize": "13px", "color": DANGER}, no_update

    # Conflict check — same table, same date and time
    if table_id:
        conflict = query(
            "SELECT * FROM reservations WHERE table_id=? AND date=? AND time=? AND status NOT IN ('Cancelled','Completed')",
            (table_id, res_date, res_time)
        )
        if not conflict.empty:
            return f"⚠️ Table already booked at {res_time} on {res_date}. Choose another table or time.", \
                   {"fontSize": "13px", "color": DANGER}, no_update

    created = date.today().isoformat()
    execute(
        "INSERT INTO reservations (customer_name, phone, email, date, time, party_size, table_id, status, special_requests, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (name, phone, email or "", res_date, res_time,
         party, table_id, "Confirmed", requests or "", created)
    )
    # Re-query so the new row appears with its real auto-generated ID
    df = query("SELECT * FROM reservations ORDER BY date DESC, time DESC")
    return f"✅ Reservation confirmed for {name} on {res_date} at {res_time}.", \
           {"fontSize": "13px", "color": SUCCESS}, \
           build_reservations_table(df)


@app.callback(
    Output("res-upd-msg", "children"),
    Output("res-upd-msg", "style"),
    Output("reservations-table", "children", allow_duplicate=True),
    Input("btn-update-res", "n_clicks"),
    State("upd-id",     "value"),
    State("upd-status", "value"),
    prevent_initial_call=True
)
def update_reservation(n, res_id, new_status):
    if not n: return no_update, no_update, no_update
    if not res_id or not new_status:
        return "⚠️ Enter a reservation ID and select a status.", \
               {"fontSize": "13px", "color": DANGER}, no_update
    existing = query("SELECT * FROM reservations WHERE reservation_id=?", (res_id,))
    if existing.empty:
        return f"⚠️ Reservation #{res_id} not found.", \
               {"fontSize": "13px", "color": DANGER}, no_update
    execute("UPDATE reservations SET status=? WHERE reservation_id=?",
            (new_status, res_id))
    df = query("SELECT * FROM reservations ORDER BY date DESC, time DESC")
    return f"✅ Reservation #{res_id} updated to {new_status}.", \
           {"fontSize": "13px", "color": SUCCESS}, \
           build_reservations_table(df)


@app.callback(
    Output("reservations-table", "children"),
    Input("filter-status", "value"),
    prevent_initial_call=False
)
def filter_reservations(status):
    if status == "All":
        df = query("SELECT * FROM reservations ORDER BY date DESC, time DESC")
    else:
        df = query("SELECT * FROM reservations WHERE status=? ORDER BY date DESC, time DESC",
                   (status,))
    return build_reservations_table(df)




@app.callback(
    Output("page-content", "children", allow_duplicate=True),
    Input({"type": "tbl-avail",    "index": ALL}, "n_clicks"),
    Input({"type": "tbl-reserved", "index": ALL}, "n_clicks"),
    Input({"type": "tbl-maint",    "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def update_table_status(avail_clicks, reserved_clicks, maint_clicks):
    from dash import ctx
    if not ctx.triggered:
        return no_update

    triggered = ctx.triggered[0]
    prop_id   = triggered["prop_id"]
    n_clicks  = triggered["value"]

    if not n_clicks:
        return no_update

    import json
    # prop_id looks like: {"index":3,"type":"tbl-avail"}.n_clicks
    id_part = prop_id.split(".n_clicks")[0]
    try:
        id_dict   = json.loads(id_part)
        table_id  = id_dict["index"]
        btn_type  = id_dict["type"]
    except Exception:
        return no_update

    status_map = {
        "tbl-avail":    "Available",
        "tbl-reserved": "Reserved",
        "tbl-maint":    "Maintenance",
    }
    new_status = status_map.get(btn_type, "Available")
    execute("UPDATE tables SET status=? WHERE table_id=?", (new_status, table_id))
    return page_tables()

if __name__ == "__main__":
    print("\n🍷 Ekhaya Restaurant Management System starting...")
    print("   Open http://127.0.0.1:8050 in your browser")
    print("   Press Ctrl+C to stop\n")
    app.run(debug=True)
