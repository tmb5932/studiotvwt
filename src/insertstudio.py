import os
import csv
import time
import psycopg2
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

STATEMENTS = []

def makeSQLStatement():
    global STATEMENTS
    path = "C:\\Users\\tstur\\PycharmProjects\\studiotvwt\\src\\companies.csv"
    with open(path) as file:
        csv_reader = csv.reader(file)
        header = True
        studioid = 0

        for row in csv_reader:
            if header:
                header = False
                continue
            title = row[0]
            sql_statement = (studioid, title)
            STATEMENTS.append(sql_statement)
            studioid = studioid + 1

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
                INSERT INTO studio (studioid, name) VALUES (%s, %s)
                """

            curs.executemany(insert_query, STATEMENTS)
            conn.commit()
            print("All studios inserted successfully!")
            conn.close()


    except:
        print("Connection failed")



def main():
    makeSQLStatement()
    sshTunnel()



if __name__ == "__main__":
    main()