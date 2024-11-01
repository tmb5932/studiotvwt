import sys, os
import argparse
import csv
from _csv import reader

#import pandas as pd


def main(): # run with parameters IMDB-Movie-Data.csv and it will read it
	#	parser = argparse.ArgumentParser("movies")
	#parser.add_argument('csv_file')
	#args = parser.parse_args()
	#df = pd.read_csv(args.csv_file)
	#print(df)

	with open("../../data/netflix_titles.csv", encoding="utf-8") as c:
		csv_reader = csv.reader(c)

		# skips first row / inits movieid
		header = True
		movieid = 1
		# print("INSERT INTO movie (movieid, title, runtime, mpaa) VALUES " , end="")
		for row in csv_reader:
			if header:
				header= False
				continue

			if (row[1] == "Movie"):
				title = row[2]
				runtimemins = row[9]
				runtimemins = runtimemins.strip().split(",")
				runtimemins = runtimemins[0]
				rating = row[8]
				if(rating == "TV-MA"):
					rating = "R"
				if(rating == "TV-14"):
					rating = "PG-13"
				if(rating == "TV-G"):
					rating = "G"
				if(rating == "TV_PG"):
					rating = "PG"
				if(rating == "TV-Y7"):
					rating = "G"

				sql_statement = ("INSERT INTO movie (movieid, title, runtime) VALUES (" + str(movieid) + ", '" + title + "', " + runtimemins + ", '" + rating + "'"  + ")")

				print(sql_statement)
				#print("(" + str(movieid) + ", '" + title + "', " + runtimemins + ", '" + rating + "'), ", end="")
				movieid = movieid + 1



if __name__ == '__main__':
	main()

