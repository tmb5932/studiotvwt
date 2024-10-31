import os
import csv
import time
import psycopg2
import random
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv




def makeSQLStatement():
    statements = []
    path = "C:\\Users\\tstur\\PycharmProjects\\studiotvwt\\src\\Collections.csv"
    with open(path) as file:
        csv_reader = csv.reader(file)
        collectionid = 0
        for row in csv_reader:
            name = row[0]
            userid = random.randint(0, 498)
            statements.append((userid, collectionid, name))
            collectionid = collectionid + 1
    return statements

def sshtunnel():
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
            statements = makeSQLStatement()
            insert_query = """
                INSERT INTO collection (userid, collectionid, name) VALUES (%s, %s, %s)
                """

            curs.executemany(insert_query, statements)
            conn.commit()
            print("All collections inserted successfully!")
            conn.close()


    except:
       print("Connection failed")



def main():
    sshtunnel()


if __name__ == "__main__":
    main()
