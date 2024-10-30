import os
import time

import psycopg2
from sshtunnel import SSHTunnelForwarder

from dotenv import load_dotenv
from tmdbv3api import TMDb, Person, Movie


def insert_production(curs, valuesArray):
    insert_query = """
    INSERT INTO "productionteam" (productionid, firstname, lastname)
    VALUES (%s, %s, %s)
    """
    curs.executemany(insert_query, valuesArray)

def fetch_actor_names_from_tmdb(api_key, num_names=1000):
    tmdb = TMDb()
    tmdb.api_key = api_key
    tmdb.language = 'en'

    person = Person()
    actor_names = set()

    page = 1

    while len(actor_names) < num_names:
        try:
            actors = person.popular(page=page)
            for actor in actors:
                name_parts = actor.name.split()

                # Get both first and last names
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[1:]
                    actor_tuple = (first_name, last_name)

                    # Add the tuple to the set if unique
                    if actor_tuple not in actor_names:
                        actor_names.add(actor_tuple)

                    # Break the loop if we've reached the required number of names
                    if len(actor_names) >= num_names:
                        break
            # go to next page
            page += 1
        except Exception as e:
            print(f"Error fetching actor names from TMDb: {e}")
            break

    return list(actor_names)

def fetch_director_names_from_tmdb(api_key, num_names):
    tmdb = TMDb()
    tmdb.api_key = api_key
    tmdb.language = 'en'

    movie = Movie()
    director_names = set()
    page = 1

    while len(director_names) < num_names:
        try:
            # Get popular movies
            popular_movies = movie.popular(page=page)
            for movie_item in popular_movies:
                # Fetch credits for the movie
                movie_credits = movie.credits(movie_item.id)

                # Extract director(s) from the crew
                for crew_member in movie_credits['crew']:
                    if crew_member['job'] == 'Director':
                        name_parts = crew_member['name'].split()

                        # Get first & last names
                        if len(name_parts) >= 2:
                            first_name = name_parts[0]
                            last_name = name_parts[1]

                            # Add the director as a tuple to the set
                            director_tuple = (first_name, last_name)

                            # Add to set if unique
                            if director_tuple not in director_names:
                                director_names.add(director_tuple)

                            if len(director_names) >= num_names:
                                break

            page += 1

        except Exception as e:
            print(f"Error fetching director names from TMDb: {e}")
            break

    return list(director_names)


def generate_and_insert_production(already_inserted, num_actors, insert_actor):
    try:
        load_dotenv()
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        api_key = os.getenv("TMDB_API_KEY")
        if not api_key:
            print("TMDb API key is missing. Please set it in your environment variables.")
            return
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

            if (insert_actor):
                names = fetch_actor_names_from_tmdb(api_key, num_names=num_actors)
                if not names:
                    print("Failed to fetch actor names from TMDb.")
                    return
            else:
                names = fetch_director_names_from_tmdb(api_key, num_actors)
                if not names:
                    print("Failed to fetch director names from TMDb.")
                    return

            # Insert actors into the database
            for production_id, (first_name, last_name) in enumerate(names, start=0):
                valuesArray.append((production_id + already_inserted, first_name, last_name))

                # Commit every 50 actors to avoid large transactions
                if production_id % 50 == 0:
                    insert_production(curs, valuesArray)
                    conn.commit()
                    valuesArray.clear()

                    print(f"Inserted {production_id} actors successfully.")
                    time.sleep(10)

            # Insert any remaining actors
            insert_production(curs, valuesArray)
            conn.commit()
            print(f"All {num_actors} new actors inserted successfully! Last id= {already_inserted + num_actors - 1}")

            conn.close()
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.close()
    finally:
        if 'curs' in locals():
            curs.close()
        if 'conn' in locals():
            conn.close()
        print("Resources cleaned up successfully.")

if __name__ == "__main__":
    amount_to_add = 250
    last_id_in_database = 0
    # to insert actors, true. to insert directors, false
    insert_actors = False
    generate_and_insert_production(last_id_in_database + 1, amount_to_add, insert_actors)