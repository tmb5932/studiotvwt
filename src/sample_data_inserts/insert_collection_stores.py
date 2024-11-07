import os
import random
import psycopg2
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

def altMakeSQLStatement():
    statements = []
    for userid in range(0, 1100):
        # IDK how all these numbers got missed for userid's but whatever -_-
        if userid in range(1000, 1051) or userid in range(598, 651) or userid in range(700, 751) or userid in range(800, 851) or userid in range(900, 951) or userid == 413 or userid == 497:
            continue
        for collectionid in range(0, 3):
            for movieid in range(0, 4):
                movie = random.randint(0, 999)
                if(userid, movie, collectionid) not in statements:
                    statements.append((userid, movie, collectionid))
    return statements

def makeSQLStatement():
    statements = []
    for collection in range(0,138):
        user = random.randint(0, 1100)
        for j in range(9):
            movie = random.randint(0, 999)
            if(user, movie, collection) not in statements:
                statements.append((user, movie, collection))
    return statements

def sshTunnel():
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
            insert_query = """
                INSERT INTO collectionstores (userid, movieid, collectionid) VALUES (%s, %s, %s)
                """
            statements = altMakeSQLStatement()
            try:
                curs.executemany(insert_query, statements)
                conn.commit()
                print("All collection storage relations inserted successfully!")
            except Exception as e:
                print(f"Failed: {e}")
                conn.rollback()  # Rollback the transaction for this batch

            conn.close()


    except:
        print("Connection failed")



def main():
    sshTunnel()



if __name__ == "__main__":
    main()