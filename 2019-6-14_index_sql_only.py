import logging
from enum import Enum

from peewee import Database, MySQLDatabase, PostgresqlDatabase, SqliteDatabase
from vnpy.trader.utility import get_file_path

logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Driver(Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"


def init(driver: Driver, settings: dict):
    init_funcs = {
        Driver.SQLITE: init_sqlite,
        Driver.MYSQL: init_mysql,
        Driver.POSTGRESQL: init_postgresql,
    }
    assert driver in init_funcs

    db = init_funcs[driver](settings)
    return db


def init_sqlite(settings: dict):
    database = settings["database"]
    path = str(get_file_path(database))
    db = SqliteDatabase(path)
    return db


def init_mysql(settings: dict):
    keys = {"database", "user", "password", "host", "port"}
    settings = {k: v for k, v in settings.items() if k in keys}
    db = MySQLDatabase(**settings)
    return db


def init_postgresql(settings: dict):
    keys = {"database", "user", "password", "host", "port"}
    settings = {k: v for k, v in settings.items() if k in keys}
    db = PostgresqlDatabase(**settings)
    return db


def fetch_indexes(driver: Driver, db: Database, table_name: str):
    if driver is Driver.SQLITE:
        c = db.execute_sql(f"PRAGMA index_list({table_name});")
        res = c.fetchall()
        res = [i[1] for i in res]
        return res
    elif driver is Driver.POSTGRESQL:
        c = db.execute_sql(
            f"SELECT indexname "
            f" FROM pg_indexes"
            f" WHERE tablename = '{table_name}';"
        )
        return [i[0] for i in c.fetchall()]
    else:
        c = db.execute_sql(
            f"SELECT DISTINCT INDEX_NAME"
            f" FROM INFORMATION_SCHEMA.STATISTICS"
            f" WHERE TABLE_NAME = '{table_name}';"
        )
        return [i[0] for i in c.fetchall()]


def create_index_if_not_exists(driver: Driver, db: Database, table_name: str, index_name: str,
                               *args):
    indexes = fetch_indexes(driver, db, table_name)
    if index_name not in indexes:
        if driver is Driver.POSTGRESQL:
            # psql does'nt supports ``
            keys = ",".join([
                f'"{key}"'
                for key in args
            ])
            db.execute_sql(f'CREATE UNIQUE INDEX "{index_name}" '
                           f' ON "{table_name}" ({keys});')
        else:
            # mysql needs ``, others supports ``
            keys = ",".join([
                f'`{key}`'
                for key in args
            ])
            db.execute_sql(f'CREATE UNIQUE INDEX `{index_name}` '
                           f' ON `{table_name}` ({keys});')


def drop_index_if_exists(driver: Driver, db: Database, table_name: str, index_name: str):
    if driver is Driver.MYSQL:
        # mysql needs DROP ... ON
        indexes = fetch_indexes(driver, db, table_name)
        if index_name in indexes:
            db.execute_sql(f"DROP INDEX `{index_name}` ON `{table_name}`;")
        return
    else:
        db.execute_sql(f'DROP INDEX  IF EXISTS  "{index_name}";')
        return


def upgrade(driver: Driver, db: Database):
    create_index_if_not_exists(driver, db,
                               'dbbardata',
                               'dbbardata_symbol_exchange_interval_datetime',
                               "symbol", "exchange", "interval", "datetime",
                               )
    drop_index_if_exists(driver, db,
                         'dbbardata',
                         'dbbardata_datetime_interval_symbol_exchange')

    create_index_if_not_exists(driver, db,
                               'dbtickdata',
                               'dbtickdata_symbol_exchange_datetime',
                               "symbol", "exchange", "datetime",
                               )
    drop_index_if_exists(driver, db,
                         'dbtickdata',
                         'dbtickdata_datetime_symbol_exchange')
    
    print("upgrade succeed!")


def downgrade(driver: Driver, db: Database):
    create_index_if_not_exists(driver, db, 'dbbardata',
                               'dbbardata_datetime_interval_symbol_exchange',
                               "datetime", "interval", "symbol", "exchange",
                               )
    drop_index_if_exists(driver, db, "dbbardata", "dbbardata_symbol_exchange_interval_datetime")

    create_index_if_not_exists(driver, db, 'dbtickdata',
                               'dbtickdata_datetime_symbol_exchange',
                               "datetime", "symbol", "exchange",
                               )
    drop_index_if_exists(driver, db, "dbtickdata", "dbtickdata_symbol_exchange_datetime")

    print("downgrade succeed!")


def main():
    from vnpy.trader.setting import get_settings

    settings = get_settings("database.")
    driver = Driver(settings["driver"])
    if driver is not Driver.MONGODB:
        db = init(driver, settings=settings)
        upgrade(driver, db)
    else:
        raise NotImplementedError()


if __name__ == '__main__':
    main()
