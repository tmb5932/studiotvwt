import os
import csv
import time
import random
import psycopg2
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv


def makeSQLStatement():
    statements = []
    for movie in range(0,999):
        platform = random.randint(1, 79)
        year = str(random.randint(1950, 2024))
        month = str(random.randint(1,12))
        day = str(random.randint(1, 28))
        if int(month) < 10:
            month = "0" + month
        if int(day) < 10:
            day = "0" + day
        statements.append((movie, platform, year + "-" + month + "-" + day))


    return statements

def sshTunnel():
    try:
        # load_dotenv()
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
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
                INSERT INTO moviereleases (movieid, platformid, releasedate) VALUES (%s, %s, %s)
                """
            statements = makeSQLStatement()
            curs.executemany(insert_query, statements)
            conn.commit()
            print("All movie-release date relations inserted successfully!")
            conn.close()


    except:
        print("Connection failed")



def main():
    sshTunnel()



if __name__ == "__main__":
    main()