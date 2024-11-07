import os
import csv
import time

import psycopg2
import random
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv


def altMakeSQLStatement():
    statements = []
    file = "../../data/collection_names2.csv"
    with open(file) as f:
        csv_reader = csv.reader(f)
        userid = 0
        collectionid = 0
        for row in csv_reader:
                name = row[0]
                statements.append((userid, collectionid, name))
                collectionid = collectionid + 1
                if collectionid >= 3:
                    collectionid = 0
                    userid += 1
                if userid == 1104:
                    break
    return statements


def makeSQLStatement():
    statements = []
    path = "C:\\Users\\tstur\\PycharmProjects\\studiotvwt\\src\\Collections.csv"
    with open(path) as file:
        csv_reader = csv.reader(file)
        collectionid = 0
        for row in csv_reader:
            name = row[0]
            userid = random.randint(0, 1100)
            statements.append((userid, collectionid, name))
            collectionid = collectionid + 1
    return statements

def sshtunnel():
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
            statements = altMakeSQLStatement()
            insert_query = """
                INSERT INTO collection (userid, collectionid, name) VALUES (%s, %s, %s)
                """
            print(statements)
            start = 0
            while start < len(statements):
                end = start + 50
                batch = statements[start:end]

                try:
                    curs.executemany(insert_query, batch)
                    conn.commit()
                    start = end
                    print(f"Inserted {min(end, len(statements))} collections successfully.")
                    time.sleep(2)  # Wait after each batch
                except Exception as e:
                    print(f"Failed to insert batch starting at index {start}: {e}")
                    conn.rollback()  # Rollback the transaction for this batch
                    break

            curs.executemany(insert_query, statements)
            conn.commit()
            print("All collections inserted successfully!")
            conn.close()


    except:
       print("Connection failed")



def main():
    sshtunnel()
    # print(altMakeSQLStatement())

if __name__ == "__main__":
    main()
