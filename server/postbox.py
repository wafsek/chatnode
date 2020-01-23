import sqlite3

conn = sqlite3.connect('../store/messages.db')
c = conn.cursor()


def create_messages_table():
    with conn:
        c.execute("""
        CREATE TABLE messages(
        from_email text ,
        to_email text,
        size INTEGER ,
        message text
        )
        """)


def create_people_table():
    with conn:
        c.execute("""
        CREATE TABLE people(
        email text PRIMARY KEY ,
        password text
        )""")


def insert_message(message):
    with conn:
        c.execute("INSERT INTO messages VALUES (:from_email,:to_email, :size, :message)",
                  {
                      'from_email': message["from_email"],
                      'to_email': message["to_email"],
                      'size': message["size"],
                      'message': message["message"]
                  })


def check_password(email, password):
    with conn:
        sql = """SELECT * FROM people
                 WHERE email='{}' AND password='{}'""".format(email, password)
        c.execute(sql)
        row = c.fetchone()
        if row:
            return password == row[1]
        else:
            return False


def insert_person(person):
    with conn:
        try:
            c.execute("INSERT INTO people VALUES (:email, :password)", {
                        'email': person.email,
                      'password': person.password, })
        except sqlite3.IntegrityError:
            return "User already exits"
        except sqlite3.Error:
            return "Something went wrong"
    show_table("people")
    return "All signed up"


def show_table(table_name):
    with conn:
        sql = "SELECT * FROM " + table_name
        c.execute(sql)
        result = c.fetchall()
        for i in result:
            print(i)


def fetch_messages():
    with conn:
        sql = """SELECT * FROM messages
                 WHERE to_email='olanordmann@gmail.com'"""
        c.execute(sql)
        rows = c.fetchall()
    return rows


def fetch_messages_to_email(to_email):
    with conn:
        sql = """SELECT * FROM messages
                 WHERE to_email='{}'""".format(to_email)
        c.execute(sql)
        rows = c.fetchall()
    return rows


def initial_setup():
    create_messages_table()
    create_people_table()

