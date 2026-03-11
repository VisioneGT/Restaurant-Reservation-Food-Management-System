"""
database/setup_db.py
────────────────────
Creates the SQLite database and loads all CSV data.
Run first before launching the dashboard.
"""

import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data")
DB_PATH  = os.path.join(BASE_DIR, "restaurant.db")


def setup():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    # ── Tables ────────────────────────────────────────────────────────
    c.executescript("""
        CREATE TABLE IF NOT EXISTS tables (
            table_id     INTEGER PRIMARY KEY,
            table_number TEXT NOT NULL UNIQUE,
            capacity     INTEGER NOT NULL,
            location     TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'Available'
        );

        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id   INTEGER PRIMARY KEY,
            customer_name    TEXT NOT NULL,
            phone            TEXT NOT NULL,
            email            TEXT,
            date             TEXT NOT NULL,
            time             TEXT NOT NULL,
            party_size       INTEGER NOT NULL,
            table_id         INTEGER,
            status           TEXT NOT NULL DEFAULT 'Pending',
            special_requests TEXT,
            created_at       TEXT NOT NULL,
            FOREIGN KEY (table_id) REFERENCES tables(table_id)
        );

        CREATE TABLE IF NOT EXISTS menu (
            item_id         INTEGER PRIMARY KEY,
            name            TEXT NOT NULL,
            category        TEXT NOT NULL,
            price           REAL NOT NULL,
            description     TEXT,
            is_available    INTEGER DEFAULT 1,
            is_vegetarian   INTEGER DEFAULT 0,
            is_halaal       INTEGER DEFAULT 0,
            prep_time_mins  INTEGER DEFAULT 15
        );

        CREATE TABLE IF NOT EXISTS inventory (
            item_id          INTEGER PRIMARY KEY,
            ingredient       TEXT NOT NULL,
            unit             TEXT NOT NULL,
            quantity_in_stock REAL NOT NULL,
            minimum_stock    REAL NOT NULL,
            unit_cost        REAL NOT NULL,
            supplier         TEXT,
            last_restocked   TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id       INTEGER PRIMARY KEY,
            reservation_id INTEGER,
            item_id        INTEGER,
            item_name      TEXT NOT NULL,
            category       TEXT NOT NULL,
            quantity       INTEGER NOT NULL,
            unit_price     REAL NOT NULL,
            order_date     TEXT NOT NULL,
            FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id),
            FOREIGN KEY (item_id) REFERENCES menu(item_id)
        );
    """)

    # ── Load CSVs ─────────────────────────────────────────────────────
    tables_df = pd.read_csv(os.path.join(DATA_DIR, "tables.csv"))
    tables_df.to_sql("tables", conn, if_exists="replace", index=False)

    res_df = pd.read_csv(os.path.join(DATA_DIR, "reservations.csv"))
    res_df["reservation_id"] = res_df["reservation_id"].astype(int)
    res_df["table_id"] = res_df["table_id"].astype(int)
    # Use INSERT with explicit reservation_id so SQLite tracks the sequence properly
    c.execute("DELETE FROM reservations")
    for _, row in res_df.iterrows():
        c.execute(
            "INSERT INTO reservations (reservation_id, customer_name, phone, email, date, time, party_size, table_id, status, special_requests, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (int(row["reservation_id"]), row["customer_name"], row["phone"],
             row["email"] if pd.notna(row["email"]) else "",
             row["date"], row["time"], int(row["party_size"]),
             int(row["table_id"]), row["status"],
             row["special_requests"] if pd.notna(row["special_requests"]) else "",
             row["created_at"])
        )
    conn.commit()

    menu_df = pd.read_csv(os.path.join(DATA_DIR, "menu.csv"))
    menu_df.to_sql("menu", conn, if_exists="replace", index=False)

    inv_df = pd.read_csv(os.path.join(DATA_DIR, "inventory.csv"))
    inv_df.to_sql("inventory", conn, if_exists="replace", index=False)

    ord_df = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"))
    ord_df.to_sql("orders", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

    print("✅ Database setup complete")
    print(f"   Tables       : {len(tables_df)}")
    print(f"   Reservations : {len(res_df)}")
    print(f"   Menu items   : {len(menu_df)}")
    print(f"   Inventory    : {len(inv_df)}")
    print(f"   Orders       : {len(ord_df)}")
    print(f"   Location     : {DB_PATH}")


if __name__ == "__main__":
    setup()
