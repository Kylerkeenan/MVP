from db.database import run_sql_file


if __name__ == '__main__':
    run_sql_file('db/init.sql')
    print('Database initialized')
