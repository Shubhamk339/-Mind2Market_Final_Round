"""
Constants used throughout the trading simulation application.
"""

# Industries available in the game
INDUSTRIES = ["Cement", "Energy", "Iron", "Aluminium", "Wood"]

# Initial balance for each team
INITIAL_BALANCE = 250000

# Number of teams per industry
TEAMS_PER_INDUSTRY = 4

# Total number of teams
TOTAL_TEAMS = 20

# Game statuses
class GameStatus:
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"

GAME_STATUSES = [
    GameStatus.NOT_STARTED,
    GameStatus.RUNNING,
    GameStatus.PAUSED,
    GameStatus.ENDED
]

# Transaction types
class TransactionType:
    PURCHASE = "purchase"
    SALE = "sale"
    SECRET_TRADE = "secret_trade"
    GIFT = "gift"
    PRODUCTION_COST = "production_cost"
    ADJUSTMENT = "adjustment"

TRANSACTION_TYPES = [
    TransactionType.PURCHASE,
    TransactionType.SALE,
    TransactionType.SECRET_TRADE,
    TransactionType.GIFT,
    TransactionType.PRODUCTION_COST,
    TransactionType.ADJUSTMENT
]

# Trade request statuses
class TradeStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

TRADE_STATUSES = [
    TradeStatus.PENDING,
    TradeStatus.ACCEPTED,
    TradeStatus.REJECTED,
    TradeStatus.CANCELLED
]

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "gamemaster"
DEFAULT_ADMIN_PASSWORD = "gamemaster369"
DEFAULT_ADMIN_NAME = "GameMaster"

# Random allocation range for initial raw units
MIN_INITIAL_RAW_UNITS = 10
MAX_INITIAL_RAW_UNITS = 50

# Auto-refresh interval in milliseconds (for leaderboard)
AUTO_REFRESH_INTERVAL = 5000  # 5 seconds

# Company Team Definitions
# Format: {"name": "Company Name", "username": "companyname", "password": "companyname+year"}
# 4 teams per industry = 20 total teams

COMPANY_TEAMS = {
    "Cement": [
        {"name": "UltraTech Cement", "username": "ultratechcement", "password": "ultratechcement1983"},
        {"name": "ACC Limited", "username": "acclimited", "password": "acclimited1936"},
        {"name": "Ambuja Cements", "username": "ambujacements", "password": "ambujacements1983"},
        {"name": "Shree Cement", "username": "shreecement", "password": "shreecement1979"},
    ],
    "Energy": [
        {"name": "Reliance Energy", "username": "relianceenergy", "password": "relianceenergy1973"},
        {"name": "Tata Power", "username": "tatapower", "password": "tatapower1919"},
        {"name": "Adani Power", "username": "adanipower", "password": "adanipower1996"},
        {"name": "NTPC Limited", "username": "ntpclimited", "password": "ntpclimited1975"},
    ],
    "Iron": [
        {"name": "Tata Steel", "username": "tatasteel", "password": "tatasteel1907"},
        {"name": "JSW Steel", "username": "jswsteel", "password": "jswsteel1982"},
        {"name": "SAIL", "username": "sail", "password": "sail1954"},
        {"name": "Jindal Steel", "username": "jindalsteel", "password": "jindalsteel1979"},
    ],
    "Aluminium": [
        {"name": "Hindalco", "username": "hindalco", "password": "hindalco1958"},
        {"name": "Vedanta Aluminium", "username": "vedantaaluminium", "password": "vedantaaluminium1976"},
        {"name": "NALCO", "username": "nalco", "password": "nalco1981"},
        {"name": "Balco", "username": "balco", "password": "balco1965"},
    ],
    "Wood": [
        {"name": "Century Plyboards", "username": "centuryplyboards", "password": "centuryplyboards1986"},
        {"name": "Greenply Industries", "username": "greenplyindustries", "password": "greenplyindustries1990"},
        {"name": "Kitply Industries", "username": "kitplyindustries", "password": "kitplyindustries1982"},
        {"name": "Archidply Industries", "username": "archidplyindustries", "password": "archidplyindustries1976"},
    ],
}
