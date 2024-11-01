import os
import random
import time

import psycopg2
from sshtunnel import SSHTunnelForwarder

from dotenv import load_dotenv

def insert_directs(curs, valuesArray):
    insert_query = """
    INSERT INTO "moviedirects" (movieId, productionid)
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
            movies = set(range(0, 1000))

            for productionid in range(1000, 1249):

                for num in range(0, random.randint(1, 5)):
                    random_movie = random.choice(list(movies))
                    valuesArray.append((random_movie, productionid))
                    movies.remove(random_movie)

                # Commit every 40 directors to avoid large transactions
                if productionid % 40 == 0:
                    insert_directs(curs, valuesArray)
                    conn.commit()
                    valuesArray.clear()
                    print(f"Inserted {productionid - 1000} directors movie relations successfully.")
                    time.sleep(5)

            insert_directs(curs, valuesArray)
            conn.commit()
            valuesArray.clear()

            i = 0
            while movies:
                director = random.randint(1000, 1250)
                random_movie = movies.pop()
                valuesArray.append((random_movie, director))
                i += 1
                if i % 50 == 0:
                    insert_directs(curs, valuesArray)
                    conn.commit()
                    valuesArray.clear()
                    print(f"Inserted {i} directors movie relations successfully.")
                    time.sleep(5)

            insert_directs(curs, valuesArray)
            # Final commit for any remaining values
            conn.commit()
            print(f"All movie director relations inserted successfully!")

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

