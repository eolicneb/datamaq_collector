from decouple import config

DB_HOST = config('DB_HOST', default=None)
DB_USER = config('DB_USER', default=None)
DB_PASSWORD = config('DB_PASSWORD', default=None)
DB_NAME = config('DB_NAME', default=None)
DB_PORT = config('DB_PORT', default=3306)
READING_TABLE = config('READING_TABLE', default="readings")
