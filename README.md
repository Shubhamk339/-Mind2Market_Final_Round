# Trading Simulation Web App

A real-time multi-team trading simulation web application built with Python, Streamlit, and SQLite.

## Features

- **20 Teams** across 5 industries (Cement, Energy, Iron, Aluminium, Wood)
- **Real-time Leaderboard** with auto-refresh
- **Marketplace** for selling material units
- **Bilateral Trade Requests** with secret deal option
- **Production System** requiring raw materials from other industries
- **Admin Panel** for game management
- **Excel Export** for full game snapshots

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
streamlit run app/main.py
```

### 3. Default Login Credentials

**Admin:**
- Username: `admin`
- Password: `admin123`

**Teams (after creation):**
- Username: `team1`, `team2`, ... `team20`
- Password: `team1123`, `team2123`, ... `team20123`

## Project Structure

```
app/
├── main.py                 # Entry point
├── auth.py                 # Authentication
├── database.py             # SQLAlchemy setup
├── models.py               # Database models
├── pages/
│   ├── 1_Login.py
│   ├── 2_Team_Dashboard.py
│   ├── 3_Marketplace.py
│   ├── 4_Trade_Requests.py
│   ├── 5_Leaderboard.py
│   ├── 6_Admin_Panel.py
│   └── 7_Admin_Reports.py
├── services/
│   ├── trading_service.py
│   ├── production_service.py
│   ├── gift_service.py
│   └── excel_service.py
└── utils/
    ├── constants.py
    └── helpers.py
```

## Game Rules

### Production
- To produce **N material units** of your industry:
  - Requires **N raw units** from each of the other 4 industries
  - Raw units are consumed, material units are created

### Trading
- Teams can only **sell material units** of their own industry
- Material units can be sold via:
  - **Marketplace** (public offers)
  - **Trade Requests** (bilateral deals)

### Leaderboard Ranking
1. Revenue (highest priority)
2. Profit
3. Total Production
4. Total Purchases

## Admin Functions

- Create/manage 20 teams
- Allocate initial raw units
- Send gifts (1 per team, material units only)
- Monitor all trades (including secret deals)
- Manual balance/inventory adjustments
- Game status control (Start/Pause/End)
- Export full game data to Excel

## Technologies

- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** SQLite (SQLAlchemy ORM)
- **Excel:** pandas + openpyxl
- **Authentication:** bcrypt
