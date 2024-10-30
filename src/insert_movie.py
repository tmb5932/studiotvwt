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

	with open("netflix_titles.csv", encoding='utf8') as c:
		csv_reader = csv.reader(c)

		# skips first row / inits movieid
		header = True
		movieid = 1
		for row in csv_reader:
			if (row[1] == "Movie"):
				if header:
					header= False
					continue


				title = row[2]
				runtimemins = row[9]
				strip = runtimemins.strip()
				split = strip.split(" ")
				runtimemins = split[0]
				mpaa = row[8]
				if (mpaa == "TV-MA"):
					mpaa = "R"
				if (mpaa == "TV-PG"):
					mpaa = "PG"
				if (mpaa == "TV-14"):
					mpaa = "PG-13"
				if (mpaa == "TV-G" or mpaa == "TV-Y" or mpaa == "TV-Y7"):
					mpaa = "G"
				sql_statement = ("INSERT INTO movie (movieid, title, runtime, mpaa) VALUES (" + str(movieid) + ", " + title + ", " + runtimemins + ", " + mpaa + ")")
				movieid = movieid + 1




if __name__ == '__main__':
	main()

