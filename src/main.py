"""

main.py
PDM Group 11: Studio TVWT
Command line interface to control the Movies database.

Author: Vladislav Usatii (vau3677@g.rit.edu)
Author: William Walker (wbw1991@g.rit.edu)
Author: Travis Brown (tmb5932@rit.edu)

"""
from datetime import datetime, timedelta

import psycopg2
from sshtunnel import SSHTunnelForwarder

from utils import *

# month constants for verbose ouput
MONTHS = {
	1: "January",
	2: "February",
	3: "March",
	4: "April",
	5: "May",
	6: "June",
	7: "July",
	8: "August",
	9: "September",
	10: "October",
	11: "November",
	12: "December"
}

conn, curs = None, None  # global db instance
logged_in = False # global login instance
logged_in_as = None # global userid instance

# clear screen, works for pycharm terminal
def clear_screen():
	print("\n" * 100)

# SELECT {col} FROM {table} JOIN {join} WHERE {criteria} GROUP BY {group_by} HAVING {having} ORDER BY {sort_col} LIMIT {limit}
def GET(table, col, criteria=None, limit=None, join=None, sort_col=None, group_by=None, having=None):
	try:
		query = f"SELECT {col} FROM \"{table}\""
		if join: query += f" {join}"
		if criteria: query += f" WHERE {criteria}"
		if group_by: query += f" GROUP BY {group_by}"
		if having: query += f" HAVING {having}"
		if sort_col: query += f" ORDER BY {sort_col}"
		if limit: query += f" LIMIT {limit}"
		curs.execute(query)
		return curs.fetchall()
	except Exception as e:
		print(f"GET failed: {e}")

# INSERT INTO {table} VALUES {data}
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

# UPDATE {table} SET {values} WHERE {criteria}
def UPDATE(table, values, criteria):
	try:
		query = f"UPDATE \"{table}\" SET {values}"
		if criteria: query += f" WHERE {criteria}"
		curs.execute(query)
		conn.commit()
		return True
	except Exception as e:
		print(f"UPDATE failed: {e}")

# DELETE FROM {table} WHERE {criteria}
def DELETE(table, criteria):
	try:
		query = f"DELETE FROM \"{table}\" WHERE {criteria}"
		curs.execute(query)
		conn.commit()
		return True
	except Exception as e:
		print(f"UPDATE failed: {e}")

# Create a new user account
def create_account():
	global logged_in
	global logged_in_as
	if logged_in:
		print(red.apply(f"\tAlready logged in."))
		return

	# Get account info from user
	email = (input(blue.apply("\tEnter your Email: "))).strip()
	username = (input(blue.apply("\tEnter a username: "))).strip()
	while not username:
		print(red.apply(f"\tUsername cannot be empty."))
		username = input(blue.apply("\tEnter a username: "))

	password = input(blue.apply("\tEnter a password: "))
	while not password or len(password) < 6:
		print(red.apply(f"\tPassword must be at least 6 characters"))
		password = input(blue.apply("\tEnter a password: "))

	first = input(blue.apply("\tEnter your first name: "))
	last = input(blue.apply("\tEnter your last name: "))

	email_exists = GET("user", col="userid", criteria=f"email = '{email}'")
	username_exists = GET("user", col="userid", criteria=f"username = '{username}'")
	maxid = GET("user", col=f"MAX(userid)")

	if email_exists:
		print(red.apply(f"\tAccount exists for {email}."))
		return
	if username_exists:
		print(red.apply(f"\tAccount exists for {username}."))
		return

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

# Login to an existing user account
def login(email_username, password_guess):
	# check if logged in
	global logged_in
	global logged_in_as
	if logged_in: return

	email_username = email_username.strip()
	# check if user exists
	email_exists = GET("user", col="userid, username, password", criteria=f"email = '{email_username}'")
	username_exists = GET("user", col="userid, username, password", criteria=f"username = '{email_username}'")


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
		print(green.apply("\tLogging in..."))
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

# Log out from user account
def logout():
	# check if logged in
	global logged_in
	global logged_in_as
	if logged_in:
		print(green.apply("\tLogged out."))
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

	collection_name = ""
	while not collection_name:
		collection_name = (input(blue.apply("\tEnter the Collection Name: "))).strip()
		if not collection_name:
			print(red.apply(f"\tYou must enter a collection name."))

	name_exists = GET("collection", col="name", criteria=f"name = '{collection_name}' and userid = '{logged_in_as}'")
	if name_exists:
		print(red.apply(f"\tCollection '{collection_name}' already exists."))
		return

	maxid = GET("collection", col=f"MAX(collectionid)", criteria=f"userid = '{logged_in_as}'")
	if maxid and maxid[0][0] is not None:
		maxi = maxid[0][0] + 1
	else:
		maxi = 0
	entry = {
		"userid": logged_in_as,
		"collectionid": maxi,
		"name": collection_name,
	}

	post_result = POST("collection", entry)
	if post_result:
		print(green.apply(f"\tCollection '{collection_name}' created."))
	else:
		print(red.apply("\tCollection creation failed."))

# Rename one of the users collections
def rename_collection():
	global logged_in
	global logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to edit a collection's name."))
		return

	collection_exists = []
	collection_name = ''
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

# Delete one of the users collections
def delete_collection():
	global logged_in
	global logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to delete a collection."))
		return

	collection = []
	collection_name = ''
	while not collection:
		collection_name = input(blue.apply("\tEnter Collection name to delete (or quit(q)): "))
		if collection_name == 'q':
			return

		collection = GET("collection", col="name", criteria=f"userid = '{logged_in_as}' AND name = '{collection_name}'")
		if not collection:
			print(red.apply(f"\tCollection '{collection_name}' does not exist."))

	DELETE("collection", criteria=f"userid = '{logged_in_as}' and name = '{collection_name}'")
	print(green.apply(f"\tDeleted {collection_name}."))

# View a collection (own or another persons)
def view_collection():
	self_collections = 'default'
	while self_collections.upper() != 'Y' and self_collections.upper() != 'N':
		self_collections = input(blue.apply("\tDo you want to see your collections(Y), another users collections(N), or cancel(Q): "))
		if self_collections.upper() == "Q":
			return
		if self_collections.upper() != 'Y' and self_collections.upper() != 'N':
			print(red.apply("\tInvalid Option."))

	userid = None
	if self_collections.upper() == 'Y':
		if not logged_in:
			print(red.apply("\tYou must be logged in to view your collections."))
			return
		userid = logged_in_as
	elif self_collections.upper() == 'N':
		name_exists = []
		while not name_exists:
			name = (input(blue.apply("\tEnter the User's Email or Username (or quit (q)): "))).strip()
			if name == 'Q' or name == 'q':
				return
			name_exists = GET("user", col="userid, username", criteria=f"email = '{name}'")
			if not name_exists:
				name_exists = GET("user", col="userid, username", criteria=f"username = '{name}'")
				if not name_exists:
					print(red.apply(f"\tUser '{name}' does not exist."))
		userid = name_exists[0][0]

	collection_exists = []
	collection = ''
	while not collection_exists:
		collection = input(blue.apply("\tEnter the Collection's Name (or quit(q)): "))
		if collection == 'q' or collection == 'Q':
			return
		collection_exists = GET("collection", col="userid, name", criteria=f"name = '{collection}' and userid = {userid}")
		if not collection_exists:
			print(red.apply(f"\tThe collection '{collection}' does not exist."))

	result = GET("movie", col="title, runtime, mpaa", join=f"JOIN collectionstores ON movie.movieid = collectionstores.movieid JOIN collection ON collection.collectionid = collectionstores.collectionid and collection.userid = collectionstores.userid", criteria=f"collection.name = '{collection}' and collection.userid = {userid}")

	if not result:
		print(green.apply(f"\tCollection '{collection}' has 0 movies, 0 hours and 0 minutes of total runtime."))
		return
	total_runtime = 0
	for res in result:
		total_runtime += int(res[1])

	hour = total_runtime // 60
	minute = total_runtime % 60
	print(green.apply(f"\tCollection '{collection}' has {len(result)} movies, {hour} hours and {minute} minutes of total runtime."))
	print(green.apply(f"\tTITLE, RUNTIME, MPAA"))
	for res in result:
		print(green.apply(f"\t{res}"))

# List the statistics about one of your own collections
def list_collections():
	if not logged_in:
		print(red.apply("\tYou must be logged in to list your collections."))
		return
	collections = GET("collection", "collection.name, COUNT(collectionstores.movieid), COALESCE(SUM(movie.runtime), 0)",
					  join="LEFT JOIN collectionstores on collectionstores.collectionid = collection.collectionid and collectionstores.userid = collection.userid LEFT JOIN movie on movie.movieid = collectionstores.movieid",
					  criteria=f"collection.userid = '{logged_in_as}'",group_by="collection.name", sort_col="collection.name ASC")

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

	columns = ("movie.title, productionteam.firstname, productionteam.lastname, movie.runtime, movie.mpaa, "
			   "avg(userrates.rating) AS avg_rating, moviereleases.releasedate, movie.movieid, COUNT(userwatches.userid) AS watch_count")

	table = "movie"
	join = """JOIN userrates on userrates.movieid = movie.movieid JOIN moviereleases ON movie.movieid = moviereleases.movieid JOIN 
	moviedirects ON moviedirects.movieid = movie.movieid JOIN productionteam ON moviedirects.productionid = productionteam.productionid 
	JOIN moviegenre ON movie.movieid = moviegenre.movieid JOIN genre ON moviegenre.genreid = genre.genreid JOIN movieproduces 
	ON movie.movieid = movieproduces.movieid JOIN studio ON movieproduces.studioid = studio.studioid JOIN userwatches ON movie.movieid = userwatches.movieid"""
	criteria = ""
	group_by = ("movie.title, productionteam.firstname, productionteam.lastname, movie.runtime, movie.mpaa, "
				"moviereleases.releasedate, movie.movieid")

	# Get user input to search by
	print(yellow.apply("\tEnter values to search by, or leave blank to ignore during search."))
	title = input(blue.apply("\tEnter the Movie's Title: "))
	release_date = ["year", "month", "day"]
	release_date[0] = input(blue.apply("\tEnter the Release Year: "))
	release_date[1] = input(blue.apply("\tEnter the Release Month in number form (feb => 02): "))
	release_date[2] = input(blue.apply("\tEnter the Release Day: "))
	cast_member = [input(blue.apply("\tEnter the Cast Members First Name: ")), input(blue.apply("\tEnter the Cast Members Last Name: "))]
	studio = input(blue.apply("\tEnter the Studio Name: "))
	genre = input(blue.apply("\tEnter the Genre Name: "))

	if title:
		criteria += f"title ILIKE '%{title}%' AND "
	if release_date:
		if release_date[0] and release_date[0].isdigit():
			criteria += f"EXTRACT(YEAR FROM moviereleases.releasedate) = {int(release_date[0])} AND "
		if release_date[1] and release_date[1].isdigit():
			criteria += f"EXTRACT(MONTH FROM moviereleases.releasedate) = {int(release_date[1])} AND "
		if release_date[2] and release_date[2].isdigit():
			criteria += f"EXTRACT(DAY FROM moviereleases.releasedate) = '{int(release_date[2])}' AND "
	if cast_member:
		join += " JOIN movieactsin ON movieactsin.movieid = movie.movieid JOIN productionteam AS cast_mem ON movieactsin.productionid = cast_mem.productionid"
		if cast_member[0]:
			criteria += f"cast_mem.firstname ILIKE '%{cast_member[0]}%' AND "
		if cast_member[1]:
			criteria += f"cast_mem.lastname ILIKE '%{cast_member[1]}%' AND "
	if studio:
		join += " "
		criteria += f"studio.name ILIKE '%{studio}%' AND "
	if genre:
		criteria += f"genre.name ILIKE '%{genre}%' AND "
	criteria = criteria.rstrip(" AND ") # this removes any hanging AND from the where clause

	# Get input on how to sort
	sorting = -1
	while sorting not in ['1', '2', '3', '4', '5']:
		sorting = input(blue.apply("Sort by Movie Title(1), Studio(2), Genre(3), Release Year(4) or Average User Rating (5)? "))
		if sorting not in ['1', '2', '3', '4', '5']:
			print(red.apply("\tInvalid Selection."))

	# Get input on ascending or descending
	sorting_by = 'default'
	while sorting_by.upper() not in ['ASC', 'DESC']:
		sorting_by = input(blue.apply("Sort by Ascending(ASC) or Descending(DESC)? "))
		if sorting_by.upper() not in ['ASC', 'DESC']:
			print(red.apply("\tInvalid Selection."))

	# SORT ON movie name, studio, genre, released year
	sort_by = sorting_by.upper()

	if sorting == '2':
		sort_col = f"studio.name {sort_by}, movie.title {sort_by}, watch_count {sort_by}"
		group_by += ", studio.name"
	elif sorting == '3':
		sort_col = f"genre.name {sort_by}, movie.title {sort_by}, watch_count {sort_by}"
		group_by += ", genre.name"
	elif sorting == '4':
		sort_col = f"moviereleases.releasedate {sort_by}, movie.title {sort_by}, watch_count {sort_by}"
	elif sorting == '5':
		sort_col = f"avg_rating {sort_by}, watch_count {sort_by}, movie.title {sort_by}"
	else:
		sort_col = f"movie.title {sort_by}, moviereleases.releasedate {sort_by}, watch_count DESC"

	result = GET(table=table, join=join, col=columns,
				 criteria=criteria, group_by=group_by, sort_col=sort_col, limit=25)
	if result:
		print(blue.apply(f"\tShowing up to 25 movies"))
		print(green.apply("\tTITLE, CAST MEMBERS, DIRECTOR, RUNTIME, MPAA, AVG USER RATING, RELEASE DATE"))
	else:
		print(green.apply("\tNo results to display!"))
		return

	for res in result:
		res = list(res)
		res[5] = round(float(res[5]), 2)
		res = tuple(res)
		cast = GET(table='productionteam', col="productionteam.firstname, productionteam.lastname", join="JOIN movieactsin ON productionteam.productionid = movieactsin.productionid", criteria=f'movieactsin.movieid = {res[7]}')
		actors_str = ", ".join([f"{first} {last}" for first, last in cast])

		print(green.apply(f"\t{res[0]}, [{actors_str}], {res[1]} {res[2]}, {res[3]} MIN, {res[4]}, {res[5]} STARS, {res[8]} WATCHES, {res[6]}"))

# Add a movie to an existing collection (your own)
def add_to_collection():
	global logged_in
	global logged_in_as

	if not logged_in:
		print(red.apply("\tYou must be signed in to add to a collection."))
		return

	coll_exists = []
	collection = ''
	while not coll_exists:
		collection = input(blue.apply("\tEnter full name of Collection to add the movie to (or quit(q)): "))
		if collection == 'q':
			return
		coll_exists = GET("collection", col="name, collectionid", criteria=f"name = '{collection}' and userid = {logged_in_as}")
		if not coll_exists:
			print(red.apply(f"\tYou have no collection with name '{collection}'!"))

	while True:
		movie = input(blue.apply("\tEnter full name of movie to add (or quit(q)): "))
		if movie.upper() == 'Q':
			print("Movie addition process ended.")
			break

		movie_exists = GET("movie", col="movieid, title", criteria=f"title = '{movie}'")
		if not movie_exists:
			print(red.apply(f"\tNo movie exists with name {movie}!"))
			continue

		entry = {"collectionid": coll_exists[0][1], "userId": logged_in_as, "movieId": movie_exists[0][0]}

		post_result = POST("collectionstores", entry)
		if post_result:
			print(green.apply(f"\t'{movie}' added to collection '{collection}'."))
		else:
			print(red.apply("\tMovie addition to collection failed."))

# Remove a movie from a collection (your own)
def remove_from_collection():
	global logged_in
	global logged_in_as

	if not logged_in:
		print(red.apply("\tYou must be signed in to remove from a collection."))
		return

	collection_exists = []
	collection = ''
	while not collection_exists:
		collection = input(blue.apply("\tEnter the Collection Name to Remove From (or quit(q)): "))
		if collection == 'q':
			return
		collection_exists = GET("collection", col="name, collectionid", criteria=f"name = '{collection}'")
		if not collection_exists:
			print(red.apply(f"\tYou have no collection with name {collection}!"))

	movie_exists = []
	movie = ''
	while not movie_exists:
		movie = input(blue.apply("\tEnter full name of movie to remove (or quit(q)): "))
		if movie == 'q':
			return
		movie_exists = GET("movie", col="movieid", criteria=f"title = '{movie}'")
		if not movie_exists:
			print(red.apply(f"\tNo movie exists with name {movie}!"))

	DELETE("collectionstores", criteria=f"collectionid = '{collection_exists[0][1]}' and userid = {logged_in_as} and movieid = {movie_exists[0][0]}")
	print(green.apply(f"\tRemoved '{movie}' from collection '{collection}'."))

# Follow another user
def follow():
	global logged_in
	global logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to follow another user."))
		return

	while True:
		followed_email = (input(blue.apply("\tEnter the email of the user to follow (or quit(q)): "))).strip()
		if followed_email.lower() == 'q':
			print(blue.apply("\tFollow process canceled."))
			return

		followed_user = GET("user", col="userid", criteria=f"email = '{followed_email}'")
		if not followed_user:
			print(red.apply(f"\tUser {followed_email} does not exist."))
			continue
		elif followed_user[0][0] == logged_in_as:
			print(red.apply(f"\tYou cannot follow yourself."))
			continue

		followedid = followed_user[0][0]
		query = {
			"followerid": logged_in_as,
			"followedid": followedid
		}
		already_following = GET("userfollows", col="followerid, followedid", criteria=f"followerid = {logged_in_as} AND followedid = {followedid}")
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

# Unfollow a followed user
def unfollow():
		global logged_in
		global logged_in_as
		if not logged_in:
			print(red.apply("\tYou must be signed in to unfollow a user."))
			return

		while True:
			followed_email = (input("Enter the email of the user to unfollow (or quit(q)): ")).strip()
			if followed_email.lower() == 'q':
				print("Unfollow process canceled.")
				return

			followed_user = GET("user", col="userid", criteria=f"email = '{followed_email}'")
			if not followed_user:
				print(f"User {followed_email} does not exist.")
				continue

			followedid = followed_user[0][0]

			is_following = GET("userfollows", col="followerid, followedid",
									criteria=f"followerid = {logged_in_as} AND followedid = {followedid}")
			if not is_following:
				print(red.apply(f"\tNot following {followed_email}."))
				return

			DELETE("userfollows", criteria=f"followerid = {logged_in_as} and followedid = {followedid}")
			print(green.apply(f"\tUnfollowed {followed_email}."))

# Rate a movie
def userrates():
	global logged_in, logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to rate a movie."))
		return

	while True:
		# Prompt for movie name
		movie_name = input(blue.apply("\tEnter the movie name (or quit(q)): "))
		if movie_name == 'q':
			print(blue.apply("\tRating process canceled."))
			return

		# Check if movie exists
		movie = GET("movie", col="movieid, title", criteria=f"title = '{movie_name}'")
		if not movie:
			print(red.apply("\tMovie not found. Please enter a proper name (check for typos)."))
			continue  # Prompt for movie name again
		else:
			break

	update_flag = False
	rating_exists = GET(table="userrates", col="rating", criteria=f"movieid = {movie[0][0]} and userid = {logged_in_as}")
	if rating_exists:
		while True:
			print(yellow.apply(f"\tYou have previously rated this movie as a {rating_exists[0][0]}."))
			change = input(blue.apply("\tWould you to change your rating of the movie (Y/N): "))
			if change not in ['Y', 'y', 'N', 'n']:
				print(red.apply("\tPlease enter Y or N."))
				continue
			if change.upper() == 'N':
				return
			update_flag = True
			break

		# Loop until a valid rating
	while True:
		rating = 'default'
		while rating not in ['1', '2', '3', '4', '5']:
			rating = input(blue.apply("\tEnter your rating (1,2,3,4,5 or enter q to quit)): "))
			if rating == 'q':
				print("Rating process canceled.")
				return

			if rating not in ['1', '2', '3', '4', '5']:
				print(red.apply("\tInvalid Rating."))
		rating = int(rating)

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
	if update_flag: # if a rating from this user for this movie already exists, change it
		post_result = UPDATE("userrates", values=f"rating = {rating}", criteria=f"movieid = {movie_id} and userid = {logged_in_as}")
	else:
		post_result = POST("userrates", entry)
	if post_result:
		print(green.apply(f"\tRating added: {movie_name} - {rating} stars."))
	else:
		print(red.apply("\tFailed to add rating."))

# Watch a movie or collection
def watch():
	global logged_in, logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to watch a movie or collection."))
		return False

	while True:
		media_type = input(blue.apply('\tWatch a single Movie or Collection? (input "M" or "C" or quit(q)): '))
		if media_type.upper() == 'Q':
			print(blue.apply("\tWatch process canceled."))
			return

		if media_type.upper() not in ["M", "C"]:
			print(red.apply("\tInvalid input. Please enter 'M' or 'C'."))
		else:
			break

	watch_date = datetime.now().isoformat(' ', 'microseconds')

	if media_type.upper() == "M":
		while True:
			media_name = input(blue.apply("\tEnter the movie name ('q' to quit): "))
			if media_name == 'q':
				print(blue.apply("\tWatch process canceled."))
				return

			media = GET("movie", col="movieid", criteria=f"title = '{media_name}'")
			if not media:
				print(red.apply("\tMovie not found. Please enter a proper name (check for typos)."))
				continue
			else:
				entry = {"movieId": media[0][0], "userId": logged_in_as, "watchDate": watch_date}
				post_result = POST("userwatches", entry)
				if post_result:
					print(green.apply(f"\tMovie marked as watched: {media_name}."))
				else:
					print(red.apply("\tFailed to mark movie as watched."))
				continue

	elif media_type.upper() == "C":
		own_collection = 'default'
		while own_collection.upper() not in ['Y', 'N']:
			own_collection = input(blue.apply("\tWatch one of your collections ('Y'), or someone elses ('N') (or 'q' to quit): "))
			if own_collection.upper() == 'Q':
				print(blue.apply("\tWatch process canceled."))
				return
			if own_collection.upper() not in ['Y', 'N']:
				print(red.apply("\tInvalid input. Please enter 'Y' or 'N'."))

		if own_collection.upper() == 'N':
			user_exists = []
			while not user_exists:
				user = (input(blue.apply("\tEnter the owner of the collections email or username (or type 'q' to quit): "))).strip()
				if user.upper() == 'Q':
					print(blue.apply("\tWatch process canceled."))
					return
				user_exists = GET(table="user", col="userid", criteria=f"email = '{user}'")
				if not user_exists:
					user_exists = GET(table="user", col="userid", criteria=f"username = '{user}'")
					if not user_exists:
						print(red.apply("\tUser not found. Please enter the proper name."))
						continue
			user_id = user_exists[0][0]
		else:
			user_id = logged_in_as

		while True:
			media_name = input(blue.apply("\tEnter the collection name (or type 'q' to quit): "))
			if media_name.upper() == 'Q':
				print(blue.apply("\tWatch process canceled."))
				return

			media = GET("collection", col="name, collectionid", criteria=f"name = '{media_name}' and userid = {user_id}")
			if not media:
				print(red.apply("\tCollection not found. Please enter a proper name (check for typos)."))
				continue
			else:
				collection_id = media[0][1]
				movies = GET("collectionstores", col="collectionstores.movieid, movie.title", criteria=f"collectionid = {collection_id} and userid = {user_id}", join="JOIN movie ON movie.movieid = collectionstores.movieid")

				for movie in movies:
					movie_id = movie[0]
					entry = {"movieId": movie_id, "userId": logged_in_as, "watchDate": watch_date}
					POST("userwatches", entry)
					print(green.apply(f"\tMovie marked as watched: {movie[1]}."))

				print(green.apply(f"\tEntire collection '{media_name}' marked as watched."))
				return

# Search for users
def search_user():
	global logged_in
	if not logged_in:
		print(red.apply("\tYou must be signed in to search for a user."))
		return

	while True:
		input_chars = (input(blue.apply("\tEnter the starting characters of the email to search (or quit(Q)): "))).strip()
		if input_chars == 'q':
			print(blue.apply("\tSearch process canceled."))
			return

		users = GET("user", col="email, userid", criteria=f"email LIKE '{input_chars}%'", limit= None)
		if not users:
			print(red.apply("\tNo emails found. Try with a different input."))
			continue
		else:
			print(green.apply("\tEmails found:"))
			i = 0
			for user in users:
				i += 1
				print(green.apply("\t" + str(i) + ": " + user[0]))
			while True:
				detail_prompt = input(blue.apply("\tEnter user number for details or search again (R) (or quit (Q)): "))
				if detail_prompt == 'R' or detail_prompt == 'r':
					break
				elif detail_prompt == 'Q' or detail_prompt == 'q':
					print(blue.apply("\tSearch process canceled."))
					return
				elif detail_prompt.isdigit() and int(detail_prompt) in range(1, i + 1):
					detail_prompt = int(detail_prompt)
					break
				else:
					print(red.apply("\tInvalid input. Please enter a valid number or (R/Q)."))

			if detail_prompt == 'R' or detail_prompt == 'r':
				continue
			profile(users[detail_prompt - 1][1])

# Displays the currently logged-in Users profile
def profile(users_id):
	user_exists = GET(table='user', col="username", criteria=f"userid = {users_id}")
	if not user_exists:
		print(red.apply("\tInvalid user."))
		return
	if logged_in_as == users_id:
		username = "You have"
	else:
		username = user_exists[0][0] + " has"

	num_col_n_following = GET("user",
							  col="COUNT(DISTINCT collection.collectionid) AS collection_count, COUNT(DISTINCT userfollows.followerid) AS follower_count",
							  join="LEFT JOIN collection ON collection.userid = \"user\".userid LEFT JOIN userfollows ON \"user\".userid = userfollows.followedid",
							  criteria=f"\"user\".userid = {users_id}",
							  group_by="\"user\".userid")
	num_following = GET("userfollows", col="COUNT(userfollows.followedid)",
						criteria=f"\"user\".userid = {users_id}",
						join="JOIN \"user\" ON userfollows.followerid = \"user\".userid")
	print(green.apply(
		f"\t{username} {num_col_n_following[0][0]} Collections, {num_col_n_following[0][1]} Followers, and Follow {num_following[0][0]} User(s)"))
	while True:
		cont = input(blue.apply("\tView Top 10 Movies? (Y/N): "))
		if cont not in ['y', 'Y', 'n', 'N']:
			print(red.apply("\tInvalid input. Please enter Y or N"))
			continue
		if cont.lower() == 'n':
			return
		break

	while True:
		print(blue.apply("\tSort Top 10 Movies By:"))
		print(blue.apply("\t1) Highest Personal Rating\n\t2) Most Personally Watched\n\t3) Both"))
		option = input("\t> ")
		if option not in ['1', '2', '3']:
			print(red.apply("\tInvalid input. Please enter 1, 2, or 3."))
			continue
		option = int(option)
		break

	if option == 1:
		columns = "userrates.rating, movie.title"
		join_data = "JOIN userrates ON userrates.movieid = movie.movieid JOIN \"user\" ON userrates.userid = \"user\".userid"
		sort_column = "userrates.rating DESC, movie.title ASC"
		where = f"userrates.userid = {users_id}"
		group_by = "userrates.rating, movie.title"
	elif option == 2:
		columns = "COUNT(DISTINCT userwatches.watchdate) as watches, movie.title"
		join_data = "LEFT JOIN userwatches ON userwatches.movieid = movie.movieid LEFT JOIN \"user\" ON userwatches.userid = \"user\".userid"
		where = f"userwatches.userid = {users_id}"
		sort_column = "watches DESC, movie.title ASC"
		group_by = "movie.title"
	else:
		columns = "movie.title, COALESCE(AVG(userrates.rating), 0) AS avg_rating, COUNT(DISTINCT userwatches.watchdate) AS watches"
		join_data = f"LEFT JOIN userrates ON userrates.movieid = movie.movieid AND userrates.userid = {users_id} LEFT JOIN userwatches ON userwatches.movieid = movie.movieid AND userwatches.userid = {users_id}"
		group_by = "movie.title"
		sort_column = "watches DESC, avg_rating DESC"
		where = f"userwatches.userid = {users_id}"

	top_ten = GET(table="movie",
				  col=columns,
				  join=join_data,
				  criteria=where,
				  sort_col=f"{sort_column}",
				  group_by=group_by,
				  limit=10)

	if option == 1:
		if len(top_ten) == 0:
			print(yellow.apply(f"\t{username} not rated any movies."))
		elif len(top_ten) < 10:
			print(yellow.apply(f"\t{username} only rated {len(top_ten)} movies."))
		for movie in top_ten:
			print(green.apply(f"\t{movie[0]} STARS: {movie[1]}"))
	elif option == 2:
		for movie in top_ten:
			print(green.apply(f"\t{movie[0]} WATCHES: {movie[1]}"))
	else:
		for movie in top_ten:
			if movie[1] == 0:
				stars = 'NO RATING\t'
			else:
				stars = str(int(movie[1])) + ' STARS\t'

			print(green.apply(f"\t{movie[2]} WATCHES and {stars}: {movie[0]}"))

# 20 most popular movies in last 90 days (rolling)
def mostpopular_90days():
	# define past 90 days
	past90 = datetime.now() - timedelta(days=90)
	past90_formatted = past90.strftime('%Y-%m-%d')

	try:
		columns = "movie.title, COUNT(userwatches.movieid) as popularity_count"
		table = "movie"
		join = "JOIN userwatches ON movie.movieid = userwatches.movieid"
		criteria = f"userwatches.watchdate >= '{past90_formatted}'"
		result = GET(table=table, col=columns, join=join, criteria=criteria, group_by="movie.title", sort_col="popularity_count DESC", limit=20)

		if result:
			print(green.apply("     TOP 20 MOST POPULAR MOVIES (90 DAYS ROLLING)"))
			print(green.apply("------------------------------------------------------"))
			for movie, count in result:
				print(green.apply(f"\t{count} views:\t{movie}"))
			print() # add a new line so that it spaces list from next command request
		else:
			print(red.apply("\tNo movies found."))
	except Exception as e:
		print(red.apply(f"\tOperation failed. {e}"))


# 20 most popular movies among only my followers
def mostpopular_amongfollowers():
	# user must be signed in for this operation
	global logged_in, logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to view this recommendation."))
		return

	try:
		# request all followers of user
		followed_users = GET("userfollows", col="followedid", criteria=f"followerid = {logged_in_as}")

		# user must have follows
		if not followed_users:
			print(red.apply("\tYou must have friends in order to print the most popular movies among followers."))
			return

		followed_ids = ','.join([str(row[0]) for row in followed_users])

		# get movies watched by each of the follower ids
		columns = "movie.title, COUNT(userwatches.movieid) as popularity"
		table = "movie"
		join = f"JOIN userwatches ON movie.movieid = userwatches.movieid"
		criteria = f"userwatches.userid IN ({followed_ids})"
		group_by = "movie.title"
		sort_col = "popularity DESC"
		result = GET(table=table, col=columns, join=join, criteria=criteria, group_by=group_by, sort_col=sort_col, limit=20)
		if result:
			print(green.apply("       TOP 20 MOST POPULAR MOVIES AMONG FOLLOWED"))
			print(green.apply("---------------------------------------------------------"))
			for movie, count in result:
				print(green.apply(f"\t{count} views:\t{movie}"))
			print()
		else:
			print(red.apply("\tNo movies found among your followed. Try adding a friend."))
		
	except Exception as e:
		print(red.apply(f"\tOperation failed. {e}"))

# top 5 new releases of the calendar month
def top_five_new():
	# curr month/year and count
	year, month, limit = datetime.now().year, datetime.now().month, 5

	try:
		columns = "movie.title, moviereleases.releasedate, COUNT(userwatches.movieid) as view_count"
		table = "movie"
		join = "JOIN moviereleases ON movie.movieid = moviereleases.movieid LEFT JOIN userwatches ON movie.movieid = userwatches.movieid"
		criteria = f"EXTRACT(YEAR FROM moviereleases.releasedate) = {year} AND EXTRACT(MONTH FROM moviereleases.releasedate) = {month}"
		group_by = "movie.title, moviereleases.releasedate"
		sort_col = "view_count DESC, moviereleases.releasedate DESC"
		result = GET(table=table, col=columns, join=join, criteria=criteria, group_by=group_by, sort_col=sort_col, limit=limit)

		if result:
			print(green.apply(f"     TOP 5 NEW RELEASES FOR {MONTHS[month]}, {year}"))
			print(green.apply("---------------------------------------------------"))
			for movie, _, count in result:
				print(green.apply(f"\t{count} watches:\t{movie}"))
			print()
		else:
			print(red.apply("\tNo movies found this month."))
	except Exception as e:
		print(red.apply(f"\tOperation failed. {e}"))

# recommend movies based on play history and users with similar data
def recommendation_system():
	# user must be signed in for checking similar users and history
	global logged_in, logged_in_as
	if not logged_in:
		print(red.apply("\tYou must be signed in to get personalized recommendations."))
		return

	try:
		# get watch history
		user_watched_movies = GET("userwatches", col="DISTINCT movieid", criteria=f"userid = {logged_in_as}")
		if not user_watched_movies:
			print(red.apply("\tYou haven't watched a movie."))
			return
		movie_ids = ','.join([str(row[0]) for row in user_watched_movies])
		
		# get users who have watched those movies
		table1 = 'userwatches'
		col1   = 'DISTINCT userid'
		crit1  = f"movieid IN ({movie_ids}) AND userid != {logged_in_as}"
		similar = GET(table1, col=col1, criteria=crit1)
		if not similar:
			print(red.apply("\tNo similar users found."))
			return

		similar_user_ids = ','.join([str(row[0]) for row in similar])

		# retrieve OTHER movies from those users
		table2 = "movie"
		col2   = "movie.title, COUNT(*) as watch_count"
		join   = "JOIN userwatches ON movie.movieid = userwatches.movieid"
		crit2  = f"userwatches.userid IN ({similar_user_ids}) AND movie.movieid NOT IN ({movie_ids})"
		group_by = "movie.title"
		sort_col = "watch_count DESC"
		result = GET(table=table2, col=col2, join=join, criteria=crit2, group_by=group_by, sort_col=sort_col, limit=10)

		print(green.apply("    MOVIES RECOMMENDED FOR YOU BASED ON YOUR WATCH HISTORY"))
		print(green.apply("--------------------------------------------------------------"))
		# rank highest views from that list and return MAX 10
		if result:
			for movie, count in result:
				print(green.apply(f"\t{count} users also watched:\t{movie}"))
		else:
			print(red.apply("\tNo movie recommendations found based on similar users."))
		print()
	except Exception as e:
		print(red.apply(f"\tOperation failed. {e}"))

# recommendation system
def recommend():
	while True:
		input_chars = (input(blue.apply("\tEnter a digit corresponding to the information you would like to see:\n\t1) the top 20 most popular movies in the last 90 days (rolling)\n\t2) the top 20 most popular movies among my followers\n\t3) the top 5 new releases of the month (calendar month)\n\t4) for you: recommend movies to watch based on your play history and the play history of similar users\n\t5) QUIT/EXIT  go back to the main program\n") + "\t> ")).strip()

		if input_chars == "1":
			mostpopular_90days()
		elif input_chars == "2":
			mostpopular_amongfollowers()
		elif input_chars == "3":
			top_five_new()
		elif input_chars == "4":
			recommendation_system()
		elif input_chars == "5":
			return
		else:
			print(red.apply("\tYou must enter a valid digit (1, 2, 3, 4, OR 5)."))

# Help command message
def help_message():
	print(blue.apply("                Studio TVWT Commands"))
	print(blue.apply("-----------------------------------------------------------------------------"))
	print(blue.apply("HELP                     show this help message and exit"))
	print(blue.apply("CREATE ACCOUNT           create new account"))
	print(blue.apply("LOGIN                    log in to your account"))
	print(blue.apply("LOGOUT                   log out of your account"))
	print(blue.apply("PROFILE                  view your profile"))
	print(blue.apply("CREATE COLLECTION        create new collection"))
	print(blue.apply("LIST COLLECTIONS         lists a user's (or your own) collections"))
	print(blue.apply("RENAME COLLECTION        change your collection's name"))
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
	print(blue.apply("RECOMMEND                see recommended movies"))
	print(blue.apply("CLEAR                	   clears the screen"))
	print(blue.apply("QUIT/EXIT                quit the program"))
	print(blue.apply("-----------------------------------------------------------------------------"))

def main():
	load_dotenv()

	global conn, curs, logged_in_as, logged_in
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
					command = user_input.strip().upper()
					if command == "HELP":
						help_message()
					elif command == 'CREATE ACCOUNT':
						create_account()
					elif command == 'LOGIN':
						if logged_in:
							print(red.apply(f"\tAlready logged in."))
							continue
						email_username = input(blue.apply("\tEnter your Email or Username: "))
						password = input(blue.apply("\tEnter your Password: "))
						login(email_username, password)
					elif command == 'LOGOUT':
						logout()
					elif command == 'PROFILE':
						if not logged_in:
							print(red.apply("\tYou must be signed in to view your profile."))
							continue
						profile(logged_in_as)
					elif command == 'CREATE COLLECTION':
						create_collection()
					elif command == 'SEARCH MOVIES' or command == 'SM':
						search_movies()
					elif command == 'LIST COLLECTIONS':
						list_collections()
					elif command == 'VIEW COLLECTION':
						view_collection()
					elif command == 'ADD TO COLLECTION':
						add_to_collection()
					elif command == 'RENAME COLLECTION':
						rename_collection()
					elif command == 'DELETE COLLECTION':
						delete_collection()
					elif command == 'REMOVE FROM COLLECTION':
						remove_from_collection()
					elif command == 'FOLLOW':
						follow()
					elif command == 'UNFOLLOW':
						unfollow()
					elif command == 'RATE MOVIE':
						userrates()
					elif command == 'SEARCH USERS':
						search_user()
					elif command == "WATCH":
						watch()
					elif command == "RECOMMEND":
						recommend()
					elif command == "CLEAR":
						clear_screen()
					elif command == 'QUIT' or command == 'EXIT':
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
