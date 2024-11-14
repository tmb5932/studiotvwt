import os
import random
import psycopg2
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv


def makeSQLStatement():
    statements = []
    key = []
    for movie in range(0, 999):
        for i in range(0, random.randint(5, 100)): # adds random amount of watches for each movie
            user = random.randint(0, 1000)
            year = str(random.randint(1950, 2024))
            month = str(random.randint(1, 12))
            day = str(random.randint(1, 28))
            if int(month) < 10:
                month = "0" + month
            if int(day) < 10:
                day = "0" + day
            hour = str(random.randint(1, 23))
            if int(hour) < 10:
                hour = "0" + hour
            minutes = str(random.randint(0, 59))
            if int(minutes) < 10:
                minutes = "0" + minutes
            seconds = str(random.randint(0, 59))
            if int(seconds) < 10:
                seconds = "0" + seconds
            milliseconds = str(random.randint(100000, 999999))
            if (movie, user) not in key:
                statements.append((movie, user, year + "-" + month + "-" + day + " " + hour + ":" + minutes + ":" + seconds + "." + milliseconds))
                key.append((movie, user))
    return statements

def sshTunnel():
    try:
        load_dotenv()
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        dbName = "p320_11"

        with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                                ssh_username=username,
                                ssh_password=password,
                                remote_bind_address=('127.0.0.1', 5432)) as server:
            server.start()
            print("SSH tunnel established")

            params = {
                'database': dbName,
                'user': username,
                'password': password,
                'host': 'localhost',
                'port': server.local_bind_port
            }
            conn = psycopg2.connect(**params)
            curs = conn.cursor()
            print("Database connection established")

            insert_query = """
                INSERT INTO userwatches (movieid, userid, watchdate) VALUES (%s, %s, %s)
                """
            statements = makeSQLStatement()
            curs.executemany(insert_query, statements)
            conn.commit()
            print("All user watches inserted successfully!")
            conn.close()


    except Exception as e:
        print("Connection failed: " + str(e))



def main():
    sshTunnel()



if __name__ == "__main__":
    main()