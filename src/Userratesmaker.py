import sys, os
import argparse
import ast
import csv
from _csv import reader
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import psycopg2
import random


def read_user_ids(curs):
    curs.execute('SELECT "user".userid FROM "user"')
    return [row[0] for row in curs.fetchall()]


def read_movie_ids(curs):
    curs.execute('SELECT "movie".movieid FROM "movie"')
    return [row[0] for row in curs.fetchall()]


def insert_user_ratings(curs, user_ids, movie_ids):
    for user_id in user_ids:

        movie_id = random.choice(movie_ids)
        rating = random.randint(1, 5)

        curs.execute("INSERT INTO userrates (userid, movieid, rating) VALUES (%s, %s, %s)",
                     (user_id, movie_id, rating))


def ssh_insert_user_ratings():
    try:
        load_dotenv()
        username = os.getenv("DB_USER")
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


            user_ids = read_user_ids(curs)
            movie_ids = read_movie_ids(curs)


            insert_user_ratings(curs, user_ids, movie_ids)

            conn.commit()
            print("All user ratings inserted successfully!")
            conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    ssh_insert_user_ratings()


