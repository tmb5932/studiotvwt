import os
import random

import psycopg2
from faker import Faker
from sshtunnel import SSHTunnelForwarder

from dotenv import load_dotenv

def insert_user(curs, valuesArray):
    insert_query = """
    INSERT INTO "user" (userId, username, password, email, firstName, lastName, creationDate)
    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    """
    curs.executemany(insert_query, valuesArray)

def generate_and_insert_users(num_users):
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

            # START OF TRAVIS WORK

            fake = Faker()

            for userId in range(0, num_users):
                firstName = fake.first_name()
                lastName = fake.last_name()
                base_username = f"{firstName[0]}{lastName}"

                # possibly add numbers after username to make it a little more real
                add_number = random.choice([0, 1, 2])
                if add_number == 1:
                    username = f"{base_username}{random.randint(0, 9)}"
                elif add_number == 2:
                    username = f"{base_username}{random.randint(10, 99)}"
                else:
                    username = base_username

                email = f"{firstName.lower()}.{lastName.lower()}@{fake.free_email_domain()}"
                password = fake.password(length= (random.randint(6, 15)))

                # Insert the generated user into the database
                valuesArray.append((userId, username, password, email, firstName, lastName))
                print((userId, username, password, email, firstName, lastName))
                # Commit every 50 users to avoid large transactions
                if userId % 50 == 0:
                    # conn.commit()
                    print(f"Inserted {userId} users successfully.")

            insert_user(curs, valuesArray)
            # Final commit for any remaining users
            conn.commit()
            print(f"All {num_users} users inserted successfully!")

            # END OF TRAVIS WORK

            conn.close()
    except:
        print("Connection failed")


if __name__ == "__main__":
    n = 6
    generate_and_insert_users(n)