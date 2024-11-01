import sys, os
from _csv import reader
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import psycopg2
import random

def insert_user_follows():
    try:
        ## load_dotenv() commented so not accidently ran again.
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

            # get every user id from user
            curs.execute('SELECT "user".userid FROM "user"')
            useridlist= [row[0] for row in curs.fetchall()]



            # loop through every user and make them follow a random ammount of other userids that are also picked randomly
            for user_id in useridlist:
                all_other_user_ids = useridlist[:]
                all_other_user_ids.remove(user_id)  # You cant follow yourself

                # thought 0-5 is a good ammount of random following ammount
                numfollows = random.randint(0, 5)
                randomfollows = random.sample(all_other_user_ids, numfollows)

                # insert userid in followerid and then the follow id in followedid
                for follow_id in numfollows:
                    curs.execute("INSERT INTO Userfollows (followerId, followedId) VALUES (%s, %s)",
                                 (user_id, follow_id))

            conn.commit()
            print("It worked!")
            curs.close()
            conn.close()

    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    insert_user_follows()
