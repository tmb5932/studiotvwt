"""

main.py

Command line interface to control the Movies database.

Author: Vladislav Usatii (vau3677@g.rit.edu)

"""
import argparse
from datetime import datetime

USERS, COLLECTIONS = {}, {} # for testing

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
	args = parser.parse_args()

	if args.create_account: create_account(args.create_account[0], args.create_account[1], args.create_account[2])
	#if args.login: login(args.login[0], args.login[1])
	#if args.create_collection: create_collection(args.create_collection[0], args.create_collection[1])
	#if args.list_collections: list_collections(args.list_collections)
	#if args.search_movies: search_movies(args.search_movies[0], args.search_movies[1])


if __name__ == "__main__":
	main()
