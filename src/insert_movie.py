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

	with open("IMDB-Movie-Data.csv") as c:
		csv_reader = csv.reader(c)

		# skips first row / inits movieid
		header = True
		movieid = 1
		print("INSERT INTO movie (movieid, title, runtime) VALUES " , end="")
		for row in csv_reader:
			if header:
				header= False
				continue


			title = row[1]
			genre = row[2]
			genres = genre.split(",")
			genstr = ""
			for genre in genres:
				genstr += genre + " "
			runtimemins = row[7]

			# sql_statement = ("INSERT INTO movie (movieid, title, runtime) VALUES (" + str(movieid) + ", " + title + ", " + runtimemins + ")")
			movieid = movieid + 1
			# print(sql_statement)
			print("(" + str(movieid) + ", '" + title + "', " + runtimemins + "), ", end="")



if __name__ == '__main__':
	main()

