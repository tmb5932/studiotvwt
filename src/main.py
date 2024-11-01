"""

main.py

Command line interface to control the Movies database.

Author: Vladislav Usatii (vau3677@g.rit.edu)
Author: William Walker (wbw1991@g.rit.edu)
Author: Travis Brown (tmb5932@rit.edu)

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
		print(red.apply(f"Collection '{collection_name}' already exists."))
		return

	maxid = GET("collection", col=f"MAX(collectionid)", criteria=f"userid = '{logged_in_as}'")
	if maxid:
		newid = str(int(maxid[0][0]) + 1)
	else:
		newid = 0
	entry = {
		"userid": logged_in_as,
		"collectionid": newid,
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
	if not logged_in:
		print(red.apply("\tYou must be signed in to create a collection."))
		return

	criteria = f"name = '{old_collection_name}' AND userid = {logged_in_as}"
	result = GET("collection", col="name", criteria=criteria, limit=1)
	if result:
		values = f"name = '{new_collection_name}'"
		criteria = f"name = '{old_collection_name}'"
		update = UPDATE("collection", values=values, criteria=criteria)
		if update:
			print(green.apply(f"Updated collection name to {new_collection_name}."))
		else:
			print(red.apply(f"Could not update collection name."))
	else:
		print(red.apply(f"This is either not your collection or the old name is not correct."))

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
			print(red.apply(f"Collection '{collection_name}' does not exist."))


	DELETE("collection", criteria=f"userid = '{logged_in_as}' and name = '{collection_name}'")
	print(green.apply(f"Deleted {collection_name}."))

def view_collection():
	self_collections = input(blue.apply("\tDo you want to see your collections(Y), another users collections(N), or cancel(Q): ")).lower()
	if self_collections == "q":
		return

	userid = None
	if self_collections == 'y':
		if not logged_in:
			print(red.apply("You must be logged in to view your collections."))
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
					print(red.apply(f"User '{name}' does not exist."))
		userid = name_exists[0][0]

	collection_exists = []
	while not collection_exists:
		collection = input(blue.apply("\tEnter the Collection's Name: "))
		collection_exists = GET("collection", criteria=f"name = '{collection}' and userid = {userid}")
		if not collection_exists:
			print(red.apply(f"User {name} has no collection '{collection}'."))

	result = GET("movie", col="title, runtime, mpaa", join=f"collectionstores ON movie.movieid = collectionstores.movieid JOIN collection ON collection.collectionid = collectionstores.collectionid", criteria=f"collection.name = '{collection}'")

	if not result:
		print(green.apply(f"Collection '{collection}' does is empty."))
		return
	total_runtime = 0
	for res in result:
		total_runtime += int(res[1])

	hour = total_runtime // 60
	minute = total_runtime % 60
	print(green.apply(f"\tCollection '{collection}' {len(result)} movies, {hour} hours and {minute} minutes of total runtime."))
	print(green.apply(f"\tTITLE, RUNTIME, MPAA"))
	print(green.apply(["\t" + res for res in result[0]]))

def list_collections():
	if not logged_in:
		print(red.apply("You must be logged in to list your collections."))
		return
	collections = GET("collection", "collection.name, count(collectionstores.movieid), sum(movie.runtime)", join="collectionstores on collectionstores.collectionid = collection.collectionid and collectionstores.userid = collection.userid JOIN movie on movie.movieid = collectionstores.movieid", criteria=f"collection.userid = '{logged_in_as}'",group_by="collection.name")

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
	columns = "movie.title, movie.runtime, movie.mpaa, avg(userrates.rating)"

	method = int(input(blue.apply("\tSearch by Movie Title(1), Release Date(2), Cast Member(3), Studio(4), or Genre(5): ")))
	if method == 1:
		name = input(blue.apply("\tEnter the Movie Title: "))
		result = GET("movie", join="userrates on userrates.movieid = movie.movieid", col=columns, criteria=f"title LIKE '%{name}%'", group_by="movie.movieid", limit=25)
		if result:
			print(blue.apply(f"\tShowing up to 25 movies with '{name}' in the title."))
			print(green.apply("\tNAME, RUNTIME, MPAA, AVG USER RATING"))

	elif method == 2:
		date = None
		while date != "asc" and date != "desc":
			date = (input(blue.apply("\tSort by Release Date Ascending (ASC) or Descending (DESC): "))).lower()

		result = GET("movie", col=columns + ", moviereleases.releasedate", join= "moviereleases ON movie.movieid = moviereleases.movieid JOIN userrates on userrates.movieid = movie.movieid", sort_col='moviereleases.releasedate', sort_by=date, group_by="movie.movieid", limit=25)
		print(blue.apply(f"\tShowing 25 movies in {date.capitalize()} order."))
		print(green.apply("\tNAME, RUNTIME, MPAA, AVG USER RATING, RELEASEDATE"))

	elif method == 3:
		cast_first = input(blue.apply("\tEnter the Cast Member First Name or Leave Empty: "))
		cast_last = input(blue.apply("\tEnter the Cast Member Last Name or Leave Empty: "))

		result = GET("movie", col=columns + ", productionteam.firstname, productionteam.lastname", join="movieactsin ON movie.movieid = movieactsin.movieid JOIN productionteam ON movieactsin.productionid = productionteam.productionid JOIN userrates on userrates.movieid = movie.movieid", criteria=f"productionteam.firstname LIKE '%{cast_first}%' AND productionteam.lastname LIKE '%{cast_last}%'", group_by="movie.movieid", limit=25)
		print(blue.apply(f"\tShowing up to 25 movies with cast member '{cast_first} {cast_last}'."))
		print(green.apply("\tNAME, RUNTIME, MPAA, AVG USER RATING, CAST FIRST NAME, CAST LAST NAME"))

	elif method == 4:
		studio = input(blue.apply("\tEnter Studio Name: "))
		result = GET("movie", col=columns + ", studio.name", join=f"movieproduces ON movie.movieid = movieproduces.movieid JOIN userrates on userrates.movieid = movie.movieid JOIN studio ON movieproduces.studioid = studio.studioid", criteria=f"studio.name LIKE '%{studio}%'", group_by="movie.movieid")
		print(blue.apply(f"\tShowing all movies from {studio}."))
		print(green.apply("\tNAME, RUNTIME, MPAA, AVG USER RATING, STUDIO"))

	elif method == 5:
		genre = input(blue.apply("\tEnter Genre: "))
		result = GET("movie", col=columns + ", genre.name", join=f"moviegenre ON movie.movieid = moviegenre.movieid JOIN genre ON moviegenre.genreid = genre.genreid JOIN userrates on userrates.movieid = movie.movieid", criteria=f"genre.name LIKE '%{genre}%'", group_by="movie.movieid", limit=25)
		print(blue.apply(f"\tShowing up to 25 movies in {genre}."))
		print(green.apply("\tNAME, RUNTIME, MPAA, AVG USER RATING, GENRE"))

	for res in result:
		res = list(res)
		res[3] = round(float(res[3]), 2)
		res = tuple(res)
		print(green.apply(f"\t{res}"))

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

	movie_exists = []
	while not movie_exists:
		movie = input(blue.apply("\tEnter full name of movie to add (or quit(q)): "))
		if movie == 'q':
			return
		movie_exists = GET("movie", criteria=f"title = '{movie}'")
		if not movie_exists:
			print(red.apply(f"\tNo movie exists with name {movie}!"))


	entry = {"collectionid": coll_exists[0][1], "userId": logged_in_as, "movieId": movie_exists[0][0]}

	post_result = POST("collectionstores", entry)
	if post_result:
		print(green.apply(f"'{movie}' added to collection '{collection}'."))
	else:
		print(red.apply("Movie addition to collection failed."))


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

	DELETE("collectionstores", criteria=f"name = '{collection} and userid = {logged_in_as} and movieid = {movie_exists[0][0]}'")
	print(green.apply(f"\tRemoved '{movie}' from collection '{collection}'."))

def follow():
	global logged_in
	global logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to create a collection."))
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
				print(green.apply(f"Followed user {followed_email} successfully."))
			else:
				print(red.apply("Following user failed."))
			return
		else:
			print(red.apply("You are already following this user."))
			return

def unfollow():
		global logged_in
		global logged_in_as
		assert logged_in, red.apply("You must be logged in to unfollow a user.")

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
			try:
				query = f"DELETE FROM userfollows WHERE followerid = %s AND followedid = %s"
				curs.execute(query, (logged_in_as, followedid))
				conn.commit()
				print(green.apply(f"Unfollowed {followed_email}."))
			except Exception as e:
				print(red.apply(f"Failed to unfollow {followed_email}."))
			return


def userrates():
	global logged_in, logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to create a collection."))
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
			print(red.apply("Movie not found. Please enter a proper name (check for typos)."))
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
			print(red.apply("Invalid rating. Please enter {1,2,3,4,5}"))
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
		print(green.apply(f"Rating added: {movie_name} - {rating} stars."))
	else:
		print(red.apply("Failed to add rating."))




from datetime import datetime

def watch():
    global logged_in, logged_in_as
    if not logged_in:
        print(red.apply("\tYou must be signed in to watch a movie or collection."))
        return

    while True:
        media_type = input('Watch a single Movie or Collection? (input "movie" or "collection"): ')
        if media_type.lower() == 'q':
            print("Watch process canceled.")
            return

        if media_type not in ["movie", "collection"]:
            print("Invalid input. Please enter 'movie' or 'collection'.")
        else:
            break

    watch_date = datetime.now().isoformat(' ', 'microseconds')

    if media_type == "movie":
        while True:
            media_name = input("\tEnter the movie name ( type 'q' to quit): ")
            if media_name.lower() == 'q':
                print("Watch process canceled.")
                return

            media = GET("movie", criteria=f"title = '{media_name}'")
            if not media:
                print(red.apply("Movie not found. Please enter a proper name (check for typos)."))
                continue
            else:
                media_id = media[0][0]
                break

    elif media_type == "collection":
        while True:
            media_name = input("\tEnter the collection name (or type 'q' to quit): ")
            if media_name.lower() == 'q':
                print("Watch process canceled.")
                return

            media = GET("collection", criteria=f"name = '{media_name}'")
            if not media:
                print(red.apply("Collection not found. Please enter a proper name (check for typos)."))
                continue
            else:
                collection_id = media[0][0]
                movies = GET("movie", col="movieId", criteria=f"collectionId = {collection_id}")

                for movie in movies:
                    movie_id = movie[0]
                    movie_name = movie[1]
                    entry = {"movieId": movie_id, "userId": logged_in_as, "watchDate": watch_date}
                    post_result = POST("userwatches", entry)
                    print(green.apply(f"Movie marked as watched: {movie_name}."))

                print(green.apply(f"Entire collection '{media_name}' marked as watched."))
                return

    entry = {"movieId": media_id, "userId": logged_in_as, "watchDate": watch_date}
    post_result = POST("userwatches", entry)
    if post_result:
        print(green.apply(f"Movie marked as watched: {media_name}."))
    else:
        print(red.apply("Failed to mark movie as watched."))













def search_user():
	global logged_in
	if not logged_in:
		print(red.apply("\tYou must be signed in to create a collection."))
		return

	while True:
		input_chars = input("Enter the starting characters of the email to search (or quit(q)): ")
		if input_chars.lower() == 'quit':
			print("Search process canceled.")
			return

		users = GET("user", col="email", criteria=f"email LIKE '{input_chars}%'", limit= None)
		if not users:
			print(red.apply("No emails Try with a different input"))
			continue
		else:
			print(green.apply("Emails found:"))
			for user in users:
				print("\t" + user[0])


def help_message():
	print(blue.apply("                Studio TVWT Commands"))
	print(blue.apply("----------------------------------------------------------------"))
	print(blue.apply("HELP                     show this help message and exit"))
	print(blue.apply("CREATE ACCOUNT           create new account"))
	print(blue.apply("LOGIN                    log in to your account"))
	print(blue.apply("LOGOUT                   log out of your account"))
	print(blue.apply("CREATE COLLECTION        create new collection"))
	print(blue.apply("LIST COLLECTION          lists a user's (or your own) collections"))
	print(blue.apply("EDIT COLLECTION          change your collection's name"))
	print(blue.apply("DELETE COLLECTION        delete one of your collections"))
	print(blue.apply("SEARCH MOVIES            search movies"))
	print(blue.apply("ADD TO COLLECTION        add a movie to one of your collections"))
	print(blue.apply("REMOVE FROM COLLECTION   delete a movie from one of your collections"))
	print(blue.apply("FOLLOW                   follow another user"))
	print(blue.apply("UNFOLLOW                 unfollow another user"))
	print(blue.apply("SEARCH USER              search users by email"))
	print(blue.apply("RATE MOVIE               applies a rating to a movie"))
	print(blue.apply("WATCH	                   Watch a movie or all movies in a collection"))
	print(blue.apply("QUIT/EXIT                quit the program"))
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
					elif command == 'search movies' or command == 'sm':
						search_movies()
					elif command == 'list collections':
						list_collections()
					elif command == 'view collection':
						view_collection()
					elif command == 'add to collection':
						add_to_collection()
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
					elif command == 'remove from collection':
						remove_from_collection()
					elif command == 'follow':
						if not logged_in:
							print(red.apply(f"\tYou are not logged in."))
							continue
						follow()
					elif command == 'unfollow':
						if not logged_in:
							print(red.apply(f"\tYou are not logged in."))
							continue
						unfollow()
					elif command == 'rate movie':
						userrates()
					elif command == 'search user':
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
