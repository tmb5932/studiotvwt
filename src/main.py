"""

main.py

Command line interface to control the Movies database.

Author: Vladislav Usatii (vau3677@g.rit.edu)

"""
import argparse
from datetime import datetime

import psycopg2
from sshtunnel import SSHTunnelForwarder

from utils import *

conn, curs = None, None  # global db instance
logged_in = False # global login instance
logged_in_as = None

# SELECT * [from *]
def GET(table, col='*', criteria=None, limit=None, join=None, sort_col=None, sort_by='DESC'):
	try:
		query = f"SELECT {col} FROM \"{table}\""
		if join: query += f" JOIN {join}"
		if criteria: query += f" WHERE {criteria}"
		if sort_col: query += f" ORDER BY {sort_col} { sort_by }"
		if limit: query += f" LIMIT {limit}"
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
		return True
	except Exception as e:
		print(red.apply(f"POST failed: {e}"))

def UPDATE(table, values, criteria=None):
	try:
		query = f"UPDATE \"{table}\" SET {values}"
		if criteria: query += f" WHERE {criteria}"
		curs.execute(query)
		conn.commit()
		return True
	except Exception as e:
		print(f"UPDATE failed: {e}")

def create_account():
	# Get account info from user
	email = input(blue.apply("\tEnter your Email: "))
	username = input(blue.apply("\tEnter a username: "))
	while not username:
		print(red.apply(f"\tUsername cannot be empty."))
		username = input(blue.apply("\tEnter a username: "))

	password = input(blue.apply("\tEnter a password: "))
	while not password or len(password) < 6:
		print(red.apply(f"\tPassword must be at least 6 characters"))
		password = input(blue.apply("\tEnter a password: "))

	first = input(blue.apply("\tEnter your first name: "))
	last = input(blue.apply("\tEnter your last name: "))

	email_exists = GET("user", criteria=f"email = '{email}'")
	username_exists = GET("user", criteria=f"username = '{username}'")
	maxid = GET("user", col=f"MAX(userid)")

	if email_exists:
		print(red.apply(f"Account exists for {email}."))
		return
	if username_exists:
		print(red.apply(f"Account exists for {username}."))

	entry = {
		"userid": str(int(maxid[0][0]) + 1),
		"username": username,
		"password": encode_password(password),
		"email": email,
		"firstName": first,
		"lastName": last,
		"lastAccessDate": datetime.now(),
		"creationDate": datetime.now(),
	}

	post_result = POST("user", entry)
	if post_result:
		print(green.apply(f"Account created for {email}, {username}."))
		login(email, password)
	else:
		print(red.apply("User creation failed."))

def login(email_username, password_guess):
	# check if logged in
	global logged_in
	global logged_in_as
	if logged_in: print(f"Already logged in.")

	# check if user exists
	email_exists = GET("user", criteria=f"email = '{email_username}'")
	username_exists = GET("user", criteria=f"username = '{email_username}'")

	print(green.apply("Logging in..."))

	if not email_exists and not username_exists:
		print(red.apply("The email or username does not exist."))
		return False

	if email_exists:
		userid, username, password = email_exists[0][0], email_exists[0][1], email_exists[0][2]
	else:
		userid, username, password = username_exists[0][0], username_exists[0][1], username_exists[0][2]
	# check password
	if valid_password(password, password_guess):
		time = datetime.now()
		updated = UPDATE("user", values=f"lastaccessdate = '{time}'", criteria=f"userid = {userid}")
		if updated:
			logged_in = True
			if email_exists:
				logged_in_as = email_exists[0][0]
			elif username_exists:
				logged_in_as = username_exists[0][0]
			print(green.apply(f"Logged in to {username}'s account."))
			return True
		else:
			print(red.apply(f"Could not log in."))
	else:
		print(red.apply(f"Incorrect password."))

def logout():
	# check if logged in
	global logged_in
	global logged_in_as
	if logged_in:
		print(green.apply("Logged out."))
		logged_in_as = None
		logged_in = False
		return True
	else:
		print(red.apply("Not logged in."))
		return False

def create_collection():
	global logged_in
	global logged_in_as

	if not logged_in:
		print(red.apply("\tYou must be signed in to create a collection."))
		return False

	collection_name = input(blue.apply("\tEnter the Collection Name: "))

	name_exists = GET("collection", criteria=f"name = '{collection_name}' and userid = '{logged_in_as}'")
	if name_exists:
		print(red.apply(f"Collection '{collection_name}' already exists."))
		return

	maxid = GET("collection", col=f"MAX(collectionid)")
	entry = {
		"userid": logged_in_as,
		"collectionid": str(int(maxid[0][0]) + 1),
		"name": collection_name,
	}

	post_result = POST("collection", entry)
	if post_result:
		print(green.apply(f"Collection '{collection_name}' created."))
	else:
		print(red.apply("Collection creation failed."))

def edit_collection(old_collection_name, new_collection_name):
	global logged_in
	global logged_in_as
	assert logged_in, red.apply("You must be signed in to create a collection.")
	criteria = f"name = '{old_collection_name}' AND userid = {logged_in_as}"
	result = GET("collection", "name", criteria, limit=1)
	if result:
		values = f"name = '{new_collection_name}'"
		criteria = f"name = '{old_collection_name}'"
		update = UPDATE("collection", values, criteria)
		if update:
			print(green.apply(f"Updated collection name to {new_collection_name}."))
		else:
			print(red.apply(f"Could not update collection name."))
	else:
		print(red.apply(f"This is either not your collection or the old name is not correct."))

def delete_collection(collection_name):
	global logged_in
	global logged_in_as
	assert logged_in, red.apply("You must be logged in to delete a collection.")
	collection = GET("collection", col="userid", criteria=f"userid = '{logged_in_as}' AND name = '{collection_name}'")
	if collection:
		try:
			query = f"DELETE FROM collection WHERE userid = %s AND name = %s"
			curs.execute(query, (logged_in_as, collection_name))
			conn.commit()
			print(green.apply(f"Removed {collection_name}."))
		except Exception as e:
			print(red.apply(f"Failed to delete {collection_name}."))
	else:
		print(red.apply(f"This collection does not exist."))


#TODO: print [name, number_movies, total_movie_length]
def list_collections(username, limit=50):
	userid = GET("user", criteria=f"username = '{username}'")

	self_collections = input(blue.apply("\tDo you want to see your collections(Y), or another users collections(N): ")).lower()

	if self_collections == 'y':
		if not logged_in:
			print(red.apply("You must be logged in to search movies."))
			return False
		list_collections(logged_in_as)
	elif self_collections == 'n':
		name = input(blue.apply("\tEnter the User's Username: "))
		list_collections(name)

	collections = GET("collection", criteria=f"userid = '{userid}'", limit=50)

	print([collection for collection in collections[0]])

def search_movies():
	global logged_in
	global logged_in_as

	# search by name, release date, cast members, studio, or genre
	results = None

	method = input(blue.apply("\tSearch by Movie Name(1), Release Date(2), Cast Member(3), Studio(4), or Genre(5): "))
	if method == 1:
		name = input(blue.apply("\tEnter the Movie Name: "))
		results = GET("movie", criteria=f"title = '{name}'")
	elif method == 2:
		date = None
		while date != "asc" and date != "desc":
			date = input(blue.apply("\tSort by Release Date Ascending (ASC) or Descending (DESC): ")).lower

		results = GET("movie", join= f"moviereleases ON movie.movieid = moviereleases.movieid", sort_col='moviereleases.releasedate', sort_by=date)
	elif method == 3:
		cast_first = input(blue.apply("\tEnter the Cast Member First Name: "))
		cast_last = input(blue.apply("\tEnter the Cast Member Last Name: "))

		results = GET("movie", join=f"movieactsin ON movie.movieid = movieactsin.movieid JOIN productionteam ON movieactsin.productionid = productionteam.productionid", criteria=f"productionteam.firstname = '{cast_first}' AND productionteam.lastname = '{cast_last}'")
	elif method == 4:
		studio = input(blue.apply("\tEnter Studio Name: "))

	return results

def add_movie(collection, movie):
	pass

def delete_movie(collection, movie):
	pass

def follow(followed_username):
	global logged_in
	global logged_in_as
	assert logged_in, red.apply("You must be logged in to follow a user.")
	followed_user = GET("user", col="userid", criteria=f"username = '{followed_username}'")
	if not followed_user:
		print(f"User {followed_username} does not exist.")
		return
	followedid = followed_user[0][0]
	query = {
		"followerid": logged_in_as,
		"followedid": followedid
	}
	already_following = GET("userfollows", criteria=f"followerid = {logged_in_as} AND followedid = {followedid}")
	if not already_following:
		return_value = POST("userfollows", query)
		if return_value:
			print(green.apply("Followed user."))
			return True
		print(red.apply("Following user failed."))
		return False
	else:
		print(red.apply("You are already following this user."))
		return False

def unfollow(followed):
	global logged_in
	global logged_in_as
	assert logged_in, red.apply("You must be logged in to unfollow a user.")
	followed_user = GET("user", col="userid", criteria=f"email = '{followed}'")
	if followed_user:
		followedid = followed_user[0][0]
		try:
			query = f"DELETE FROM userfollows WHERE followerid = %s AND followedid = %s"
			curs.execute(query, (logged_in_as, followedid))
			conn.commit()
			print(green.apply(f"Unfollowed {followed}."))
		except Exception as e:
			print(red.apply(f"Failed to unfollow {followed}."))


def userrates():
	global logged_in, logged_in_as
	assert logged_in, red.apply("You must be logged in to rate a movie.")

	# prompt
	movie_name = input("Enter the movie name: ")
	rating = int(input("Enter your rating (1,2,3,4,5): "))

	movie = GET("movie", criteria=f"title = '{movie_name}'")

	# Loop until a valid movie
	while not movie:
		print(red.apply("Movie not found. Please enter a proper name (check for typos)."))
		movie_name = input("Enter the movie name (or type 'q' to quit): ")
		if movie_name == 'q':
			print("Rating process canceled.")
			return
		movie = GET("movie", criteria=f"title = '{movie_name}'")

	# Loop until a valid rating
	while rating not in [1, 2, 3, 4, 5]:
		print(red.apply("Invalid rating. Please enter {1,2,3,4 or 5}"))
		rating = input("Enter your rating (1-5, or type 'q' to quit): ")
		if rating.lower() == 'q':
			print("Rating process canceled.")
			return

	# get the movie id
	movie_id = movie[0][0]

	# Create entry
	entry = { "movieId": movie_id, "userId": logged_in_as, "rating": rating }

	# Insert the rating
	post_result = POST("userrates", entry)
	if post_result:
		print(green.apply(f"Rating added: {movie_name} - {rating} stars."))
	else:
		print(red.apply("Failed to add rating."))

def help_message():
	print(blue.apply("                Studio TVWT Commands"))
	print(blue.apply("----------------------------------------------------------------"))
	print(blue.apply("HELP                  show this help message and exit"))
	print(blue.apply("CREATE ACCOUNT        create new account"))
	print(blue.apply("LOGIN                 log in to your account"))
	print(blue.apply("LOGOUT                log out of your account"))
	print(blue.apply("CREATE COLLECTION     create new collection"))
	print(blue.apply("LIST COLLECTIONS      lists a user's (or your own) collections"))
	print(blue.apply("EDIT COLLECTION       change your collection's name"))
	print(blue.apply("DELETE COLLECTION     delete one of your collections"))
	print(blue.apply("SEARCH MOVIES         search movies"))
	print(blue.apply("ADD MOVIE             add a movie to one of your collections"))
	print(blue.apply("DELETE MOVIE          delete a movie from one of your collections"))
	print(blue.apply("FOLLOW                follow another user"))
	print(blue.apply("UNFOLLOW              unfollow another user"))
	print(blue.apply("QUIT/EXIT             quit the program"))
	print(blue.apply("----------------------------------------------------------------"))

def main():
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
				print(blue.apply("Enter a command or type HELP"))
				user_input = input("> ")
				if user_input.strip():
					command = user_input.strip().lower()
					if command == "help":
						help_message()
					elif command == 'create account':
						create_account()
					elif command == 'login':
						email_username = input(blue.apply("\tEnter your Email or Username: "))
						password = input(blue.apply("\tEnter your Password: "))
						login(email_username, password)
					elif command == 'logout':
						logout()
					elif command == 'create collection':
						create_collection()
					elif command == 'list collections':
						search_movies()
					elif command == 'add movie':
						if not logged_in:
							print(red.apply(f"\tYou are not logged in."))
							continue
						collection = input(blue.apply("\tEnter Collection Name to Add to: "))
						movie = input(blue.apply("\tEnter Movie Name to Add: "))
						add_movie(collection, movie)
					elif command == 'edit collection':
						if not logged_in:
							print(red.apply(f"\tYou are not logged in."))
							continue
						old_name = input(blue.apply("\tEnter the Collection Name to Edit: "))
						new_name = input(blue.apply("\tEnter the New Collection Name: "))
						edit_collection(old_name, new_name)
					elif command == 'delete collection':
						name = input(blue.apply("\tEnter the Collection Name to Delete: "))
						delete_collection(name)
					elif command == 'delete movie':
						collection = input(blue.apply("\tEnter the Collection Name to Remove From: "))
						movie = input(blue.apply("\tEnter the Movie Name to Remove: "))
						delete_movie(collection, movie)
					elif command == 'follow':
						if not logged_in:
							print(red.apply(f"\tYou are not logged in."))
							continue
						name = input(blue.apply("\tEnter the Username to Follow: "))
						follow(name)
					elif command == 'unfollow':
						if not logged_in:
							print(red.apply(f"\tYou are not logged in."))
							continue
						unfollow()
					elif command == 'rate movie':
						userrates()
					elif command == 'quit' or command == 'exit':
						# close connection
						curs.close()
						conn.close()
						break
	except Exception as e:
		print(f"Db connection error: {e}")

if __name__ == "__main__":
	main()
