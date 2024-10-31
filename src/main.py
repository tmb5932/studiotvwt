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
from datetime import datetime

from utils import *

conn, curs = None, None  # global db instance
logged_in = False # global login instance
logged_in_as = None

class CustomArgumentParser(argparse.ArgumentParser):
	def exit(self, status=0, message=None):
		if message: self._print_message(message, sys.stderr)

	def error(self, message):
		self.print_usage(sys.stderr)
		self.exit(status=2, message=f'{self.prog}: error: {message}\n')

# SELECT * [from *]
def GET(table, col='*', criteria=None):
	try:
		query = f"SELECT {col} FROM \"{table}\""
		if criteria: query += f" WHERE {criteria}"
		curs.execute(query)
		return curs.fetchall()
	except Exception as e:
		print(f"GET failed: {e}")

# INSERT INTO 
def POST(table, data):
	try:
		cols = ', '.join(data.keys())
		values = ', '.join([f"%({key})s" for key in data.keys()])
		query = f"INSERT INTO \"{table}\" ({cols}) VALUES ({values})"
		curs.execute(query, data)
		conn.commit()
		print(green.apply(f"Inserted into {table}: {data}"))
		return True
	except Exception as e:
		print(red.apply(f"POST failed: {e}"))

def create_account(email, password, username, first=None, last=None):
	result = GET("user", criteria=f"email = '{email}'")
	maxd = GET("user", col=f"MAX(userid)")
	if result:
		print(red.apply(f"Account exists for {email}."))
		return
	entry = {
		"userid": str(int(maxd[0][0]) + 1),
		"username": username,
		"password": encode_password(password),
		"email": email,
		"firstName": None,
		"lastName": None,
		"lastAccessDate": datetime.now(),
		"creationDate": datetime.now(),
	}

	if first: entry["firstName"] = first
	if last: entry["lastName"] = last
	post_result = POST("user", entry)
	if post_result:
		print(green.apply(f"Account created for {email}, {username}."))
		login(email, password)
	else:
		print(red.apply("User creation failed."))

def login(email, password_guess):
	# check if logged in
	global logged_in
	global logged_in_as
	if (logged_in): print(f"Already logged in.")

	# check if user exists
	result = GET("user", criteria=f"email = '{email}'")
	if result:
		username = result[0][1]
		password = result[0][2]
		# check password
		if valid_password(password, password_guess):
			logged_in = True
			logged_in_as = result[0]
			print(green.apply(f"Logged in to {username}'s account."))

def logout():
	# check if logged in
	global logged_in
	global logged_in_as
	if (logged_in_as and logged_in):
		logged_in = False
		logged_in_as = None
		print(green.apply("Logged out."))
		return
	print(red.apply("Not logged in."))
	return

def create_collection(collection_name):
	assert logged_in, red.apply("You must be signed in to create a collection.")

	maxd = GET("collection", col=f"MAX(collectionid)")
	entry = {
		"userid": logged_in_as[0],
		"collectionid": str(int(maxd[0][0]) + 1),
		"name": collection_name,
	}

	post_result = POST("collection", entry)

def main():
	parser = CustomArgumentParser(description="Movie Database Application") # cmds
	parser.add_argument('--create-account', help="create new account", nargs=5, metavar=('EMAIL', 'PASSWORD', 'USERNAME', 'FIRST', 'LAST'))
	parser.add_argument('--login', help="log in to your account", nargs=2, metavar=('EMAIL', 'PASSWORD'))
	parser.add_argument('--logout', help="log out of your account", action='store_true')
	parser.add_argument('--create-collection', help="create new collection", nargs=1, metavar=('COLLECTION'))
	parser.add_argument('--list-collections', help="list collections", nargs=1, metavar=('USERNAME'))
	parser.add_argument('--search-movies', help="search movies", nargs=2, metavar=('QUERY', 'CRITERIA'))
	parser.add_argument('--add-movie', help="add movie to collection", nargs=2, metavar=('COLLECTION', 'MOVIE'))
	parser.add_argument('--delete-collection', help="delete collection", nargs=1, metavar=('COLLECTION'))
	parser.add_argument('--follow', help="follow user", nargs=1, metavar=('USERNAME'))
	parser.add_argument('--unfollow', help="unfollow user", nargs=1, metavar=('USERNAME'))
	parser.add_argument('--terminate', help="terminate program", action='store_true')

	load_dotenv() # env

	global conn, curs
	try:
		username = os.getenv("DB_USERNAME")
		password, censored = os.getenv("DB_PASSWORD"), '*' * len(os.getenv("DB_PASSWORD"))
		dbName = "p320_11"
		addr, port = '127.0.0.1', 5432
		print(f"Authorization details:\nUsername: {username}\tPassword: {censored}\nDB Name: {dbName}\tAddress: {addr}:{port}")

		with SSHTunnelForwarder(('starbug.cs.rit.edu', 22), ssh_username=username, ssh_password=password, remote_bind_address=(addr, port)) as server:
			server.start()
			print("SSH tunnel established.")
			params = {
				'database': dbName,
				'user': username,
				'password': password,
				'host': 'localhost',
				'port': server.local_bind_port
			}
			conn = psycopg2.connect(**params)
			curs = conn.cursor()
			print("DB connection established.")

			# main loop
			while True:
				user_input = input("> ")
				if user_input.strip():
					args = parser.parse_args(user_input.split())
					if args.create_account:
						create_account(*args.create_account)
					elif args.login:
						login(*args.login)
					elif args.create_collection:
						create_collection(*args.create_collection)
					elif args.list_collections:
						list_collections(*args.list_collections)
					elif args.search_movies:
						search_movies(*args.search_movies)
					elif args.add_movie:
						add_movie(*args.add_movie)
					elif args.delete_collection:
						delete_collection(*args.delete_collection)
					elif args.follow:
						follow(*args.follow)
					elif args.unfollow:
						unfollow(*args.unfollow)
					elif args.terminate:
						# close connection
						curs.close()
						conn.close()
						break
	except Exception as e:
		print(f"Db connection error: {e}")

if __name__ == "__main__":
	main()

