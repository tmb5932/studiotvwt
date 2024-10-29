"""

main.py

Command line interface to control the Movies database.

Author: Vladislav Usatii (vau3677@g.rit.edu)

"""
import sys, os, random
import argparse
from datetime import datetime
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import psycopg2

conn, curs = None, None  # global db instance

# connect to server once
def db_connect():
	global conn, curs
	try:
		username = os.getenv("DB_USERNAME")
		password, censored = os.getenv("DB_PASSWORD"), '*' * len(os.getenv("DB_PASSWORD"))
		dbName = "p320_11"
		addr, port = '127.0.0.1', 5432
		print(f"Login:\nUsername: {username}\tPassword: {censored}\nDB Name: {dbName}\tAddress: {addr}:{port}")

		with SSHTunnelForwarder(('starbug.cs.rit.edu', 22), ssh_username=username, ssh_password=password, remote_bind_address=(addr, port)) as server:
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
			print("db connection established")
	except Exception as e:
		print(e)
		print("connection failed")

# SELECT * [from *]
def GET(table, col='*', criteria=None):
	try:
		query = f"SELECT {col} FROM {table}"
		if criteria: query += f" WHERE {criteria}"
		curs.execute(query)
		results = curs.fetchall()
		for row in results: print(row)
	except Exception as e:
		print("GET failed: {e}")

# INSERT INTO 
def POST(table, data):
	try:
		cols = ', '.join(data.keys())
		values = ', '.join([f"%({key})s" for key in data.keys()])
		query = f"INSERT INTO {table} ({cols}) VALUES ({values})"
		curs.execute(query, data)
		conn.commit()
		print(f"Inserted into {table}: {data}")
	except Exception as e:
		print(f"POST failed: {e}")

def create_account(email, password, username):
	result = GET("users", criteria=f"email = '{email}'")
	if result:
		print(f"Account exists for {email}")
	else:
		POST("users", {"email": email, "password": password, "username": username})
		print(f"Account created for {email}, {username}")

def main():
	parser = argparse.ArgumentParser(description="Movie Database Application")

	# cmds
	parser.add_argument('--create-account', help="create new account", nargs=3, metavar=('EMAIL', 'PASSWORD', 'USERNAME'))
	parser.add_argument('--login', help="log in to your account", nargs=2, metavar=('EMAIL', 'PASSWORD'))
	parser.add_argument('--create-collection', help="create new collection", nargs=2, metavar=('EMAIL', 'COLLECTION'))
	parser.add_argument('--list-collections', help="list collections", nargs=1, metavar=('USERNAME'))
	parser.add_argument('--search-movies', help="search movies", nargs=2, metavar=('QUERY', 'CRITERIA'))
	parser.add_argument('--add-movie', help="add movie to collection", nargs=3, metavar=('EMAIL', 'COLLECTION', 'MOVIE'))
	parser.add_argument('--delete-collection', help="delete collection", nargs=2, metavar=('EMAIL', 'COLLECTION'))
	parser.add_argument('--follow', help="follow user", nargs=2, metavar=('EMAIL', 'USER'))
	parser.add_argument('--unfollow', help="unfollow user", nargs=2, metavar=('EMAIL', 'USER'))

	load_dotenv()  # env
	db_connect()  # db connection

	while True:
		try:
			user_input = input("> ")
			if user_input.strip():
				args = parser.parse_args(user_input.split())
				if args.create_account: create_account(args.create_account[0], args.create_account[1], args.create_account[2])
		except (EOFError, KeyboardInterrupt):
			print("\nExiting...")
			break
		except SystemExit:
			pass
		finally:
			print("Exited.")

if __name__ == "__main__":
	main()

