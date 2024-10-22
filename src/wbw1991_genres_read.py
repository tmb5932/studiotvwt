import sys, os
import argparse
import csv
from _csv import reader


# Insert genres function
# inserts a bunch of genres and genreid read and parsed from the csv into datagrips genre table.
# params: csv_file ( IMDB-MOVIE-DATA.csv )
def readgenres(csv_file):

    # list of unique genres and the start of the genreid
    genreslist= [ ]
    genreid= 1

    # open times csv and read according to row genres is in
    with open(csv_file) as c:
        csv_reader=csv.reader(c)

        # skip header row
        header= True
        for row in  csv_reader:
            if header:
                header= False
                continue

        # get genre column from current row and split int a new list
            genrestr =  row[2]
            colgenres= genrestr.split(",")

        #loop through each genre in column, strip it down (pause) and if not in OG genres list add it to genre table
            for genre in colgenres:
                newgenre=genre.strip()
                if genre not in  genreslist:
                    genreslist.append(genre)
                    sql_statement= "INSERT INTO genre (genreid, name) VALUES ({}, '{}')".format(genreid, newgenre)
                    genreid+=1
                    print(sql_statement)


# Example main function calling the new function
def main():
    csv_file= "IMDB-Movie-Data.csv"
    readgenres(csv_file)


if __name__ == "__main__":
 main()