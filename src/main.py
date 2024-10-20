import sys, os
import argparse

import pandas as pd


def main(): # run with parameters IMDB-Movie-Data.csv and it will read it
	#	parser = argparse.ArgumentParser("movies")
	#parser.add_argument('csv_file')
	#args = parser.parse_args()
	#df = pd.read_csv(args.csv_file)
	#print(df)
	with open("IMDB-Movie-Data.csv") as csv:
		for line in csv:
			print(line)


if __name__ == '__main__':
	main()

