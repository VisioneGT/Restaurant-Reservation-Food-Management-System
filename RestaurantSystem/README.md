# 🍷 Ekhaya Restaurant Management System

A full restaurant management system built with Python, SQLite, and Dash.
Replaces manual booking records with a real-time interactive management dashboard
for a South African restaurant. Built as a portfolio project demonstrating
database design, data validation, SQL query optimisation, and interactive
dashboard development.

---

## Features

- **Reservations** — Book, confirm, update and cancel reservations with real-time
  conflict detection that prevents double-booking the same table at the same time
- **Table Management** — Track availability of 10 tables across indoor, outdoor,
  and private dining. Update status in real time
- **Menu & Inventory** — Full menu with dietary tags (vegetarian, halaal), pricing,
  and prep times. Inventory tracking with low stock alerts and visual stock level bars
- **Reports** — Busiest days analysis, top ordered dishes, monthly revenue,
  reservation status breakdown, party size distribution, and revenue by category

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| SQLite | Relational database (4 tables with foreign keys) |
| pandas | Data loading, querying, aggregation |
| Plotly | Interactive charts |
| Dash | 5-page web dashboard with URL routing |

---

## Project Structure

```
RestaurantSystem/
│
├── data/
│   ├── reservations.csv    ← 58 reservations (Jan–Mar 2024)
│   ├── tables.csv          ← 10 tables across 3 locations
│   ├── menu.csv            ← 28 menu items across 4 categories
│   ├── inventory.csv       ← 25 ingredients with stock levels
│   └── orders.csv          ← 77 order line items for reporting
│
├── database/
│   ├── setup_db.py         ← Creates SQLite DB and loads all CSVs
│   └── restaurant.db       ← Auto-generated (excluded from Git)
│
├── dashboard/
│   └── app.py              ← 5-page Dash dashboard
│
├── requirements.txt
└── README.md
```

---

## How to Run

### Step 1 — Install dependencies
```bash
pip install pandas plotly dash
```

### Step 2 — Set up the database
```bash
cd database
python setup_db.py
```

### Step 3 — Run the dashboard
```bash
cd ../dashboard
python app.py
```

Open `http://127.0.0.1:8050` in your browser.

> The dashboard will auto-run setup_db.py if the database does not exist yet.

---

## Dashboard Pages

**Home** — System overview with KPI cards and navigation

**Reservations** — Full reservations table with status filter, new booking form
with conflict detection, and update/cancel form with validation

**Tables** — Visual table cards showing real-time availability, occupancy charts,
and manual status controls for each table

**Menu & Inventory** — Complete menu with dietary tags and pricing, inventory
tracker with stock level progress bars and low stock alerts

**Reports** — 7 charts covering monthly reservations, busiest days, status
breakdown, top dishes, revenue by category, monthly revenue, and party sizes

---

## Security & Data Validation

- Double-booking prevention — checks for existing reservations at the same table,
  date and time before confirming
- Input validation on all reservation form fields before any database write
- Parameterised SQL queries throughout to prevent SQL injection
- Status-based filtering ensures cancelled reservations cannot create conflicts

---

## Skills Demonstrated

- Relational database design with foreign key relationships
- SQL queries with JOINs, filters, and aggregations
- Real-time conflict detection logic
- Form input validation before database writes
- SQL injection prevention using parameterised queries
- 5-page Dash application with URL routing and callbacks
- Interactive Plotly charts for business reporting

---

*Built with Python · SQLite · pandas · Plotly · Dash*
