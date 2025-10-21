from src.infrastructure.db_operations import *


if __name__ == "__main__":
    repo = SQLAlchemyDatabaseRepository()
    readings = list(repo.get_reading('counter_0', since=1757174469, limit=3, offset=1))
    readings += list(repo.get_reading('counter_0', limit=3, offset=4))
    for r in readings:
        print(r)
