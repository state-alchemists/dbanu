import os

CURRENT_DIR = os.path.dirname(__file__)
SQLITE_DB_PATH = os.getenv("DB_ANU_SQLITE_PATH", os.path.join(CURRENT_DIR, "sample.db"))

PG_SQL_HOST = os.getenv("DB_ANU_PG_SQL_HOST", "localhost")
PG_SQL_DATABASE = os.getenv("DB_ANU_PG_SQL_DATABASE", "dbanu_db")
PG_SQL_USER = os.getenv("DB_ANU_PG_SQL_USER", "dbanu_user")
PG_SQL_PASSWORD = os.getenv("DB_ANU_PG_SQL_PASSWORD", "dbanu_password")
PG_SQL_PORT = int(os.getenv("DB_ANU_PG_SQL_PORT", "5432"))

MYSQL_HOST = os.getenv("DB_ANU_MYSQL_HOST", "localhost")
MYSQL_DATABASE = os.getenv("DB_ANU_MYSQL_DATABASE", "dbanu_db")
MYSQL_USER = os.getenv("DB_ANU_MYSQL_USER", "dbanu_user")
MYSQL_PASSWORD = os.getenv("DB_ANU_MYSQL_PASSWORD", "dbanu_password")
MYSQL_PORT = int(os.getenv("DB_ANU_MYSQL_PORT", "3306"))
