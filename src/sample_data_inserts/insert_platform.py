import sys, os
import csv
from _csv import reader
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import psycopg2

PLATFORMSLIST = []

def read_platforms(csvfile):
    global PLATFORMSLIST
    with open(csvfile, encoding='utf-8') as c:
        csv_reader = csv.reader(c)
        header = True
        for row in csv_reader:
            if header:
                header = False
                continue
            platform = row[0].strip()
            if platform and platform not in PLATFORMSLIST:
                PLATFORMSLIST.append(platform)

def insert_platforms(curs, valuesArray):
    insert_query = """INSERT INTO platform (platformid, name) VALUES (%s, %s)"""
    curs.executemany(insert_query, valuesArray)

def ssh_insert_platforms():
    try:
        load_dotenv()
        username = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dbName = "p320_11"
        valuesArray = []
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
            csvfile = "Platforms.csv"
            read_platforms(csvfile)
            valuesArray = [(i + 1, platform) for i, platform in enumerate(PLATFORMSLIST)]
            insert_platforms(curs, valuesArray)
            conn.commit()
            print("All platforms inserted successfully!")
            conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    ssh_insert_platforms()

