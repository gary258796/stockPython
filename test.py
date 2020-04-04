

# store stock code to mysql( not uesful now )
import pymysql
import atexit
import datetime as dt

db = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    passwd="gary258976",
    db='gary-python-stock')
_connection = None


def get_connection():
    global _connection
    global db
    if not _connection:
        _connection = db.cursor()
    return _connection


def store_to_mysql():

    conn = get_connection()

    sql = "UPDATE run_to_where SET tw_progress = %s WHERE load_type = %s"
    val = (5, "tw")
    conn.execute(sql, val)

    sql = "UPDATE run_to_where SET jp_progress = %s WHERE load_type = %s"
    val = (5, "tw")
    conn.execute(sql, val)
    db.commit()
    # conn.close()
    # db.close()


# before app exit, store the progress
def store_progress_mysql(tw_int, jp_int, us_int, load_type):

    conn = get_connection()

    sql = "UPDATE run_to_where SET tw_progress = %s, jp_progress = %s, us_progress = %s WHERE load_type = %s"
    val = (tw_int, jp_int, us_int, load_type)
    conn.execute(sql, val)
    db.commit()
    conn.close()
    db.close()


def exit_handler():
    store_progress_mysql(0, 0, 0, "2m")
    print('My application is ending!')


atexit.register(exit_handler)


def main():
    print("\nStart get 2m data. \n\n")
    end = dt.date.today()
    days = dt.timedelta(59)
    start = str(end - days)
    end = str(end)
    print(end)
    print(start)


if __name__ == '__main__':
    main()



