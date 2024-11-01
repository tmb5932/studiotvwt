import csv
import os
import time

import psycopg2
from sshtunnel import SSHTunnelForwarder

from dotenv import load_dotenv

def insert_movies(curs, valuesArray):
    insert_query = """
    INSERT INTO "movie" (movieId, title, runtime, mpaa)
    VALUES (%s, %s, %s, %s)
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

            with open("../../data/netflix_titles.csv") as c:
                csv_reader = csv.reader(c)

                # skips first row / inits movieid
                header = True
                movieid = 0

                for row in csv_reader:
                        if header:
                            header = False
                            continue

                        if row[1] != "Movie":
                            continue

                        title = row[2]
                        if len(title) > 50:
                            continue
                        runtimemins = row[9]
                        runtimemins = runtimemins.strip().split(",")[0].strip().split(" ")[0]
                        mpaa = row[8]

                        if mpaa == "TV-MA":
                            mpaa = "R"
                        elif mpaa == "TV-14":
                            mpaa = "PG-13"
                        elif mpaa == "TV-G" or mpaa == "TV-Y7" or mpaa == "TV-Y":
                            mpaa = "G"
                        elif mpaa == "TV-PG":
                            mpaa = "PG"

                        valuesArray.append((movieid, title, runtimemins, mpaa))
                        movieid += 1

                        # Commit every 50 movies to avoid large transactions
                        if movieid % 50 == 0:
                            insert_movies(curs, valuesArray)
                            conn.commit()
                            valuesArray.clear()
                            print(f"Inserted {movieid} movies successfully.")
                            time.sleep(10)
                        if movieid % 1000 == 0 and movieid != 0:
                            break

            insert_movies(curs, valuesArray)
            # Final commit for any remaining movies
            conn.commit()
            print(f"All {movieid} movies inserted successfully!")

            # END OF WORK

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

