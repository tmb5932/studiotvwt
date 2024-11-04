"""

main.py
PDM Group 11: Studio TVWT
Command line interface to control the Movies database.

Author: Vladislav Usatii (vau3677@g.rit.edu)
Author: William Walker (wbw1991@g.rit.edu)
Author: Travis Brown (tmb5932@rit.edu)

"""
from datetime import datetime

import psycopg2
from sshtunnel import SSHTunnelForwarder
import math

from utils import *

conn, curs = None, None  # global db instance
logged_in = False # global login instance
logged_in_as = None # global userid instance

# SELECT * [from *]
def GET(table, col='*', criteria=None, limit=None, join=None, sort_col=None, sort_by='DESC', group_by=None):
	try:
		query = f"SELECT {col} FROM \"{table}\""
		if join: query += f" JOIN {join}"
		if criteria: query += f" WHERE {criteria}"
		if group_by: query += f" GROUP BY {group_by}"
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

def DELETE(table, criteria):
	try:
		query = f"DELETE FROM \"{table}\" WHERE {criteria}"
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
		print(red.apply(f"\tAccount exists for {email}."))
		return
	if username_exists:
		print(red.apply(f"\tAccount exists for {username}."))

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
		print(green.apply(f"\tAccount created for {email}, {username}."))
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


	if not email_exists and not username_exists:
		print(red.apply("The email or username does not exist."))
		return

	if email_exists:
		userid, username, password = email_exists[0][0], email_exists[0][1], email_exists[0][2]
	else:
		userid, username, password = username_exists[0][0], username_exists[0][1], username_exists[0][2]
	# check password
	if valid_password(password, password_guess):
		time = datetime.now()
		print(green.apply("Logging in..."))
		updated = UPDATE("user", values=f"lastaccessdate = '{time}'", criteria=f"userid = {userid}")
		if updated:
			logged_in = True
			if email_exists:
				logged_in_as = email_exists[0][0]
			elif username_exists:
				logged_in_as = username_exists[0][0]
			print(green.apply(f"\tLogged in to {username}'s account."))
			return True
		else:
			print(red.apply(f"\tCould not log in."))
	else:
		print(red.apply(f"\tIncorrect password."))

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
		print(red.apply("\tNot logged in."))
		return

def create_collection():
	global logged_in
	global logged_in_as

	if not logged_in:
		print(red.apply("\tYou must be signed in to create a collection."))
		return

	collection_name = input(blue.apply("\tEnter the Collection Name: "))

	name_exists = GET("collection", criteria=f"name = '{collection_name}' and userid = '{logged_in_as}'")
	if name_exists:
		print(red.apply(f"\tCollection '{collection_name}' already exists."))
		return

	maxid = GET("collection", col=f"MAX(collectionid)")

	entry = {
		"userid": logged_in_as,
		"collectionid": maxid[0][0] + 1,
		"name": collection_name,
	}

	post_result = POST("collection", entry)
	if post_result:
		print(green.apply(f"\tCollection '{collection_name}' created."))
	else:
		print(red.apply("\tCollection creation failed."))

def edit_collection():
	global logged_in
	global logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to edit a collection's name."))
		return

	collection_exists = []
	while not collection_exists:
		collection_name = input(blue.apply("\tEnter the Collection Name to Edit: "))
		collection_exists = GET("collection", col="name", criteria=f"name = '{collection_name}' and userid = '{logged_in_as}'")

		if not collection_exists:
			print(red.apply(f"\tCollection '{collection_name}' does not exist, or is not owned by you."))

	new_name = input(blue.apply("\tEnter the New Collection Name: "))

	update = UPDATE("collection", values=f"name = '{new_name}'", criteria=f"name = '{collection_name}'")
	if update:
		print(green.apply(f"\tUpdated collection name to {new_name}."))
	else:
		print(red.apply(f"\tCould not update collection name."))

def delete_collection():
	global logged_in
	global logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to create a collection."))
		return

	collection = []
	while not collection:
		collection_name = input(blue.apply("\tEnter Collection name to delete (or quit(q)): "))
		if collection_name == 'q':
			return

		collection = GET("collection", criteria=f"userid = '{logged_in_as}' AND name = '{collection_name}'")
		if not collection:
			print(red.apply(f"\tCollection '{collection_name}' does not exist."))


	DELETE("collection", criteria=f"userid = '{logged_in_as}' and name = '{collection_name}'")
	print(green.apply(f"\tDeleted {collection_name}."))

def view_collection():
	self_collections = None
	while self_collections != 'y' and self_collections != 'n':
		self_collections = input(blue.apply("\tDo you want to see your collections(Y), another users collections(N), or cancel(Q): ")).lower()
		if self_collections == "q":
			return
		if self_collections != 'y' and self_collections != 'n':
			print(red.apply("\tInvalid Option."))

	userid = None
	if self_collections == 'y':
		if not logged_in:
			print(red.apply("\tYou must be logged in to view your collections."))
			return
		userid = logged_in_as
	elif self_collections == 'n':
		name_exists = []
		while not name_exists:
			name = input(blue.apply("\tEnter the User's Email or Username: "))
			name_exists = GET("user", criteria=f"email = '{name}'")
			if not name_exists:
				name_exists = GET("user", criteria=f"username = '{name}'")
				if not name_exists:
					print(red.apply(f"\tUser '{name}' does not exist."))
		userid = name_exists[0][0]

	collection_exists = []
	while not collection_exists:
		collection = input(blue.apply("\tEnter the Collection's Name: "))
		collection_exists = GET("collection", criteria=f"name = '{collection}' and userid = {userid}")
		if not collection_exists:
			print(red.apply(f"\tThe collection '{collection}' does not exist."))

	result = GET("movie", col="title, runtime, mpaa", join=f"collectionstores ON movie.movieid = collectionstores.movieid JOIN collection ON collection.collectionid = collectionstores.collectionid", criteria=f"collection.name = '{collection}'")

	if not result:
		print(green.apply(f"\tCollection '{collection}' does is empty."))
		return
	total_runtime = 0
	for res in result:
		total_runtime += int(res[1])

	hour = total_runtime // 60
	minute = total_runtime % 60
	print(green.apply(f"\tCollection '{collection}' {len(result)} movies, {hour} hours and {minute} minutes of total runtime."))
	print(green.apply(f"\tTITLE, RUNTIME, MPAA"))
	for res in result:
		print(green.apply(f"\t{res}"))

def list_collections():
	if not logged_in:
		print(red.apply("\tYou must be logged in to list your collections."))
		return
	collections = GET("collection", "collection.name, count(collectionstores.movieid), sum(movie.runtime)",
					  join="collectionstores on collectionstores.collectionid = collection.collectionid and collectionstores.userid = collection.userid JOIN movie on movie.movieid = collectionstores.movieid",
					  criteria=f"collection.userid = '{logged_in_as}'",group_by="collection.name", sort_by="ASC", sort_col="collection.name")

	if not collections:
		print(green.apply("\tYou have no collections."))
		return
	print(green.apply(f"\tYou have {len(collections)} collection(s)."))
	for col in collections:
		hours = col[2] // 60
		minutes = col[2] % 60
		print(green.apply(f"\t'{col[0]}', {col[1]} movies, {hours} hours and {minutes} minutes of total runtime"))

# search by name, release date, cast members, studio, or genre
def search_movies():
	global logged_in
	global logged_in_as

	result = []
	columns = "movie.title, productionteam.firstname, productionteam.lastname, movie.runtime, movie.mpaa, avg(userrates.rating), moviereleases.releasedate, movie.movieid"

	table = "movie"
	join = f"userrates on userrates.movieid = movie.movieid JOIN moviereleases ON movie.movieid = moviereleases.movieid JOIN moviedirects ON moviedirects.movieid = movie.movieid JOIN productionteam ON moviedirects.productionid = productionteam.productionid"
	criteria = ""
	group_by = "movie.title, productionteam.firstname, productionteam.lastname, movie.runtime, movie.mpaa, moviereleases.releasedate, movie.movieid"
	sort_col = ""

	title = input(blue.apply("\tEnter the Movie's Title: "))
	release_date = ["year", "month", "day"]
	release_date[0] = input(blue.apply("\tEnter the Release Year: "))
	release_date[1] = input(blue.apply("\tEnter the Release Month: "))
	release_date[2] = input(blue.apply("\tEnter the Release Day: "))
	cast_member = ["first", "last"]
	cast_member[0] = input(blue.apply("\tEnter the Cast Members First Name: "))
	cast_member[1] = input(blue.apply("\tEnter the Cast Members Last Name: "))
	studio = input(blue.apply("\tEnter the Studio Name: "))
	genre = input(blue.apply("\tEnter the Genre Name: "))

	if not title and not release_date and not studio and not genre:
		print(blue.apply(f"\tShowing 25 recent movies."))
		print(green.apply("\tTITLE, RUNTIME, MPAA, AVG USER RATING, RELEASE DATE"))
		result = GET("movie", col=columns + ", moviereleases.releasedate",
					 join="moviereleases ON movie.movieid = moviereleases.movieid JOIN userrates on userrates.movieid = movie.movieid",
					 sort_col='moviereleases.releasedate', sort_by='asc',
					 group_by="movie.movieid, moviereleases.releasedate", limit=25)
		for res in result:
			print(green.apply(f"\t{res}"))

	# SORT ON movie name, studio, genre, released year
	if title:
		criteria += f"title LIKE '%{title}%' AND "
	if release_date:
		if release_date[0]:
			criteria += f"EXTRACT(YEAR FROM moviereleases.releasedate) = {int(release_date[0])} AND "
		if release_date[1]:
			criteria += f"EXTRACT(MONTH FROM moviereleases.releasedate) = {int(release_date[1])} AND "
		if release_date[2]:
			criteria += f"EXTRACT(DAY FROM moviereleases.releasedate) = '{int(release_date[2])}' AND "
	if cast_member:
		criteria += f"productionteam.firstname LIKE '%{cast_member[0]}%' AND productionteam.lastname LIKE '%{cast_member[1]}%' AND "
	if studio:
		join += " JOIN movieproduces ON movie.movieid = movieproduces.movieid JOIN studio ON movieproduces.studioid = studio.studioid"
		criteria += f"studio.name LIKE '%{studio}%' AND "
	if genre:
		join += " JOIN moviegenre ON movie.movieid = moviegenre.movieid JOIN genre ON moviegenre.genreid = genre.genreid"
		criteria += f"genre.name LIKE '%{genre}%' AND "
	criteria = criteria.rstrip(" AND ") # this removes any hanging AND from the where clause

	sorting = -1
	while sorting not in ['1', '2', '3', '4']:
		sorting = input(blue.apply("Sort by Movie Title(1), Studio(2), Genre(3), or Release Year(4)? "))
		if sorting not in ['1', '2', '3', '4']:
			print(red.apply("\tInvalid Selection."))

	sorting_by = 'default'
	while sorting_by.lower() not in ['asc', 'desc']:
		sorting_by = input(blue.apply("Sort by Ascending(ASC) or Descending(DESC)? "))
		if sorting_by.lower() not in ['asc', 'desc']:
			print(red.apply("\tInvalid Selection."))

	sort_by = sorting_by.lower()
	if sorting == 2:
		sort_col = "studio.name, "
	if sorting == 3:
		sort_col = "genre.name, "
	if sorting == 4:
		sort_col = "moviereleases.releasedate, movie.title"

	if sorting != 4:
		sort_col += "movie.title, moviereleases.releasedate"

	result = GET(table=table, join=join, col=columns,
				 criteria=criteria, group_by=group_by, sort_by=sort_by, sort_col=sort_col, limit=25)
	if result:
		print(blue.apply(f"\tShowing up to 25 movies"))
		print(green.apply("\tTITLE, CAST MEMBERS, DIRECTOR, RUNTIME, MPAA, AVG USER RATING, RELEASE DATE"))

	if not result:
		print(green.apply("\tNo results to display!"))

	for res in result:
		res = list(res)
		res[5] = round(float(res[5]), 2)
		res = tuple(res)
		cast = GET(table='productionteam', col="productionteam.firstname, productionteam.lastname", join="movieactsin ON productionteam.productionid = movieactsin.productionid", criteria=f'movieactsin.movieid = {res[7]}')
		actors = [f"{first} {last}" for first, last in cast]

		print(green.apply(f"\t{res[0]}, {actors}, {res[1]} {res[2]}, {res[3]}, {res[4]}, {res[5]}, {res[6]}"))


def add_to_collection():
	global logged_in
	global logged_in_as

	if not logged_in:
		print(red.apply("\tYou must be signed in to add to a collection."))
		return

	coll_exists = []
	while not coll_exists:
		collection = input(blue.apply("\tEnter full name of Collection to add the movie to (or quit(q)): "))
		if collection == 'q':
			return
		coll_exists = GET("collection", criteria=f"name = '{collection}' and userid = {logged_in_as}")
		if not coll_exists:
			print(red.apply(f"\tYou have no collection with name '{collection}'!"))

	while True:
		movie = input(blue.apply("\tEnter full name of movie to add (or quit(q)): "))
		if movie.lower() == 'q':
			print("Movie addition process ended.")
			break

		movie_exists = GET("movie", criteria=f"title = '{movie}'")
		if not movie_exists:
			print(red.apply(f"\tNo movie exists with name {movie}!"))
			continue

		entry = {"collectionid": coll_exists[0][1], "userId": logged_in_as, "movieId": movie_exists[0][0]}

		post_result = POST("collectionstores", entry)
		if post_result:
			print(green.apply(f"\t'{movie}' added to collection '{collection}'."))
		else:
			print(red.apply("\tMovie addition to collection failed."))

def remove_from_collection():
	global logged_in
	global logged_in_as

	if not logged_in:
		print(red.apply("\tYou must be signed in to remove from a collection."))
		return

	collection_exists = []
	while not collection_exists:
		collection = input(blue.apply("\tEnter the Collection Name to Remove From (or quit(q)): "))
		if collection == 'q':
			return
		collection_exists = GET("collection", criteria=f"name = '{collection}'")
		if not collection_exists:
			print(red.apply(f"\tYou have no collection with name {collection}!"))

	movie_exists = []
	while not movie_exists:
		movie = input(blue.apply("\tEnter full name of movie to remove (or quit(q)): "))
		if movie == 'q':
			return
		movie_exists = GET("movie", criteria=f"title = '{movie}'")
		if not movie_exists:
			print(red.apply(f"\tNo movie exists with name {movie}!"))

	DELETE("collectionstores", criteria=f"collectionid = '{collection_exists[0][1]}' and userid = {logged_in_as} and movieid = {movie_exists[0][0]}")
	print(green.apply(f"\tRemoved '{movie}' from collection '{collection}'."))

def follow():
	global logged_in
	global logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to follow another user."))
		return

	while True:
		followed_email = input("Enter the email of the user to follow (or quit(q)): ")
		if followed_email.lower() == 'q':
			print("Follow process canceled.")
			return

		followed_user = GET("user", col="userid", criteria=f"email = '{followed_email}'")
		if not followed_user:
			print(f"User {followed_email} does not exist.")
			continue

		followedid = followed_user[0][0]
		query = {
			"followerid": logged_in_as,
			"followedid": followedid
		}
		already_following = GET("userfollows", criteria=f"followerid = {logged_in_as} AND followedid = {followedid}")
		if not already_following:
			return_value = POST("userfollows", query)
			if return_value:
				print(green.apply(f"\tFollowed user {followed_email} successfully."))
			else:
				print(red.apply("\tFollowing user failed."))
			return
		else:
			print(red.apply("\tYou are already following this user."))
			return

def unfollow():
		global logged_in
		global logged_in_as
		if not logged_in:
			print(red.apply("\tYou must be signed in to unfollow a user."))
			return

		while True:
			followed_email = input("Enter the email of the user to unfollow (or quit(q)): ")
			if followed_email.lower() == 'q':
				print("Unfollow process canceled.")
				return

			followed_user = GET("user", col="userid", criteria=f"email = '{followed_email}'")
			if not followed_user:
				print(f"User {followed_email} does not exist.")
				continue

			followedid = followed_user[0][0]
			DELETE("userfollows", criteria=f"followerid = {logged_in_as} and followedid = {followedid}")
			print(green.apply(f"\tUnfollowed {followed_email}."))

def userrates():
	global logged_in, logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to rate a movie."))
		return

	while True:
		# Prompt for movie name
		movie_name = input("\tEnter the movie name (or quit(q)): ")
		if movie_name.lower() == 'q':
			print("Rating process canceled.")
			return

		# Check if movie exists
		movie = GET("movie", criteria=f"title = '{movie_name}'")
		if not movie:
			print(red.apply("\tMovie not found. Please enter a proper name (check for typos)."))
			continue  # Prompt for movie name again
		else:
			break

		# Loop until a valid rating
	while True:
		rating = int(input("\tEnter your rating (1,2,3,4,5 or enter q to quit)): "))
		if rating == 'q':
			print("Rating process canceled.")
			return

		if rating not in [1, 2, 3, 4, 5]:
			print(red.apply("\tInvalid rating. Please enter {1,2,3,4,5}"))
			continue
		else:
			break

	# get the movie id
	movie_id = movie[0][0]

	# Create entry
	entry = { "movieId": movie_id, "userId": logged_in_as, "rating": rating }

	# Insert the rating
	post_result = POST("userrates", entry)
	if post_result:
		print(green.apply(f"\tRating added: {movie_name} - {rating} stars."))
	else:
		print(red.apply("\tFailed to add rating."))

def watch():
	global logged_in, logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to watch a movie or collection."))
		return False

	while True:
		media_type = input('Watch a single Movie or Collection? (input "m" or "c"): ')
		if media_type.lower() == 'q':
			print("Watch process canceled.")
			return

		if media_type not in ["m", "c"]:
			print("Invalid input. Please enter 'movie' or 'collection'.")
		else:
			break

	watch_date = datetime.now().isoformat(' ', 'microseconds')

	if media_type == "m":
		while True:
			media_name = input("\tEnter the movie name ( type 'q' to quit): ")
			if media_name.lower() == 'q':
				print("Watch process canceled.")
				return

			media = GET("movie", criteria=f"title = '{media_name}'")
			if not media:
				print(red.apply("\tMovie not found. Please enter a proper name (check for typos)."))
				continue
			else:
				media_id = media[0][0]
				break

	elif media_type == "c":
		while True:
			media_name = input("\tEnter the collection name (or type 'q' to quit): ")
			if media_name.lower() == 'q':
				print("Watch process canceled.")
				return

			media = GET("collection", criteria=f"name = '{media_name}'")
			if not media:
				print(red.apply("\tCollection not found. Please enter a proper name (check for typos)."))
				continue
			else:
				collection_id = media[0][1]
				movies = GET("collectionstores", col="movieid", criteria=f"collectionid = {collection_id}")

				for movie in movies:
					movie_id = movie[0]
					movie_name = GET("movie", col="title", criteria=f"movieId = {movie_id}")
					entry = {"movieId": movie_id, "userId": logged_in_as, "watchDate": watch_date}
					post_result = POST("userwatches", entry)
					print(green.apply(f"\tMovie marked as watched: {movie_name}."))

				print(green.apply(f"\tEntire collection '{media_name}' marked as watched."))
				return

	entry = {"movieId": media_id, "userId": logged_in_as, "watchDate": watch_date}
	post_result = POST("userwatches", entry)
	if post_result:
		print(green.apply(f"\tMovie marked as watched: {media_name}."))
	else:
		print(red.apply("\tFailed to mark movie as watched."))

def search_user():
	global logged_in
	if not logged_in:
		print(red.apply("\tYou must be signed in to search for a user."))
		return

	while True:
		input_chars = input("Enter the starting characters of the email to search (or quit(q)): ")
		if input_chars.lower() == 'q':
			print("Search process canceled.")
			return

		users = GET("user", col="email", criteria=f"email LIKE '{input_chars}%'", limit= None)
		if not users:
			print(red.apply("\tNo emails Try with a different input"))
			continue
		else:
			print(green.apply("\tEmails found:"))
			for user in users:
				print("\t" + user[0])

def help_message():
	print(blue.apply("                Studio TVWT Commands"))
	print(blue.apply("-----------------------------------------------------------------------------"))
	print(blue.apply("HELP                     show this help message and exit"))
	print(blue.apply("CREATE ACCOUNT           create new account"))
	print(blue.apply("LOGIN                    log in to your account"))
	print(blue.apply("LOGOUT                   log out of your account"))
	print(blue.apply("CREATE COLLECTION        create new collection"))
	print(blue.apply("LIST COLLECTIONS         lists a user's (or your own) collections"))
	print(blue.apply("EDIT COLLECTION          change your collection's name"))
	print(blue.apply("DELETE COLLECTION        delete one of your collections"))
	print(blue.apply("SEARCH MOVIES            search movies"))
	print(blue.apply("ADD TO COLLECTION        add a movie to one of your collections"))
	print(blue.apply("REMOVE FROM COLLECTION   delete a movie from one of your collections"))
	print(blue.apply("VIEW COLLECTION          view a collection of another user (or your own)"))
	print(blue.apply("FOLLOW                   follow another user"))
	print(blue.apply("UNFOLLOW                 unfollow another user"))
	print(blue.apply("SEARCH USERS             search users by email"))
	print(blue.apply("RATE MOVIE               applies a rating to a movie"))
	print(blue.apply("WATCH                    watch a movie or all movies in a collection"))
	print(blue.apply("QUIT/EXIT                quit the program"))
	print(blue.apply("-----------------------------------------------------------------------------"))

def main():
	load_dotenv()

	global conn, curs
	try:
		username = os.getenv("DB_USERNAME")
		password, censored = os.getenv("DB_PASSWORD"), '*' * len(os.getenv("DB_PASSWORD"))
		dbName = "p320_11"
		addr, port = '127.0.0.1', 5432
		# print(f"Authorization details:\nUsername: {username}\tPassword: {censored}\nDB Name: {dbName}\tAddress: {addr}:{port}")
		print("Application Started!")
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
					elif command == 'search movies' or command == 'sm':
						search_movies()
					elif command == 'list collections':
						list_collections()
					elif command == 'view collection':
						view_collection()
					elif command == 'add to collection':
						add_to_collection()
					elif command == 'edit collection':
						edit_collection()
					elif command == 'delete collection':
						delete_collection()
					elif command == 'remove from collection':
						remove_from_collection()
					elif command == 'follow':
						follow()
					elif command == 'unfollow':
						unfollow()
					elif command == 'rate movie':
						userrates()
					elif command == 'search users':
						search_user()
					elif command == "watch":
						watch()
					elif command == 'quit' or command == 'exit':
						# close connection
						curs.close()
						conn.close()
						break
					else:
						print(red.apply(f"\t{command} is not a valid command!"))
	except Exception as e:
		print(f"Db connection error: {e}")

if __name__ == "__main__":
	main()
