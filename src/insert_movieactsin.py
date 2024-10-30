import csv
import os
import random
import time

import psycopg2
from sshtunnel import SSHTunnelForwarder

from dotenv import load_dotenv

def insert_acts_in(curs, valuesArray):
    insert_query = """
    INSERT INTO "movieactsin" (movieId, productionid)
    VALUES (%s, %s)
    """
    curs.executemany(insert_query, valuesArray)

def generate_movies():
    try:
        load_dotenv()
        username = os.getenv("DB_USERNAME")
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

            # START OF WORK
            # im really sorry that this effectively brute forces with overlaps but i didn't want to figure out better solution
            # surprisingly even with 1000 actors to choose from with a 2nd chance still got 2 overlap errors
            for movieid in range(0, 1000):

                for num in range(0, random.randint(3, 7)):
                    rand = random.randint(0, 1000)
                    for value in valuesArray:
                        if value == (movieid, rand):
                            rand = random.randint(0, 1000)
                    valuesArray.append((movieid, rand))


                # Commit every 40 movies to avoid large transactions
                if movieid % 40 == 0:
                    insert_acts_in(curs, valuesArray)
                    conn.commit()
                    valuesArray.clear()
                    print(f"Inserted {movieid} movies actor relations successfully.")
                    time.sleep(2)

            insert_acts_in(curs, valuesArray)
            # Final commit for any remaining values
            conn.commit()
            print(f"All {movieid} movies actor relations inserted successfully!")

            # END OF TRAVIS WORK

    except Exception as e:
        print(f"Error: {e}")
        conn.close()
    finally:
        if curs:
            curs.close()
        if conn:
            conn.close()
        print("Resources cleaned up successfully.")

if __name__ == '__main__':
    generate_movies()

