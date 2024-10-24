"""

main.py

Command line interface to control the Movies database.

Author: Vladislav Usatii (vau3677@g.rit.edu)

"""
import sys, os, random
import argparse
from datetime import datetime
from dotenv import load_dotenv

def GET():
	pass

def POST():
	pass

def create_account(email, password, username):
	censored = '*' * len(password)
	if email in USERS:
		print(f"account exists for {email} and {censored}")
	else:
		USERS[email] = {'created_at': datetime.now(), 'last_login': None, 'collections': {}, 'following': []}
		print(f"account created for {email}")

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

	# init db
	try:
		load_dotenv()
		username = os.getenv("DB_USERNAME")
		password = os.getenv("DB_PASSWORD")
		dbName = "p320_11"
		valuesArr = []

		with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
			ssh_username=username, ssh_password=password,
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
			print("db connection established")

	# parse args
	args = parser.parse_args()

	if args.create_account: create_account(args.create_account[0], args.create_account[1], args.create_account[2])
	#if args.login: login(args.login[0], args.login[1])
	#if args.create_collection: create_collection(args.create_collection[0], args.create_collection[1])
	#if args.list_collections: list_collections(args.list_collections)
	#if args.search_movies: search_movies(args.search_movies[0], args.search_movies[1])


if __name__ == "__main__":
	main()
