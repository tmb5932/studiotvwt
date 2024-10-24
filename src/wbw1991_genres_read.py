import sys, os
import argparse
import ast
import csv
from _csv import reader

GENRESLIST = []

# Insert genres function IMDB MOVIE DATA CSV
# inserts a bunch of genres and genreid read and parsed from the csv into datagrips genre table.
# params: csvfile ( IMDB-MOVIE-DATA.csv )
def readgenres(csvfile):

    # list of unique genres and the start of the genreid
    global GENRESLIST
    genreid= len(GENRESLIST) + 1

    # open times csv and read according to row genres is in
    with open(csvfile) as c:
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
                if genre not in  GENRESLIST:
                    GENRESLIST.append(genre)
                    sql_statement= "INSERT INTO genre (genreid, name) VALUES ({}, '{}')".format(genreid, newgenre)
                    genreid+=1
                    print(sql_statement)



# Insert genres functionmovies_metadata.csv
# Inserts a bunch of genres and genreid read and parsed from the csv into datagrips genre table.
# params: csvfile (movies_metadata.csv)
def readgenres2(csvfile):

    global GENRESLIST
    genreid = len(GENRESLIST) + 1


    # Open the CSV file and read according to row genres is in
    #only works with utf-8 encoding :shrug:
    with open(csvfile, encoding='utf-8') as c:
        csv_reader = csv.reader(c)
        # Skip header row
        header = True
        for row in csv_reader:
            if header:
                header = False
                continue

            genrestr= row[3]
            genreincol1 =  genrestr.strip("[]")  # strip brackets
            genreincol2 =  genreincol1.split("}, {")  # Split into individual

            for genre in genreincol2:
                genre = genre.strip("{}") #strip curlies
                genres = genre.split(", ")
                for names in genres:
                    if "'name': " in names:
                        # Split the string and get genre name
                        namepart= names.split(": ")[1]
                        genrename= namepart.strip("'\"")

                        #if not already in genreslist
                        if genrename not in GENRESLIST:

                            # the movie_metadata.csv changes midway and the row for genre is swapped. terrible csv wth...
                            # everything after carousel prods is not a genre and a studio instead so im stopping it here
                            # the csv changes for no reason where the column genre is in is different :sob: :why:
                            if genrename == 'Carousel Productions':
                                return


                            GENRESLIST.append(genrename)
                            sql_statement = "INSERT INTO genre (genreid, name) VALUES ({}, '{}')".format(genreid, genrename)
                            genreid += 1
                            print(sql_statement)


# Example main function calling the new function
def main():
    csvfile= "IMDB-Movie-Data.csv"
    csvfile2= "movies_metadata.csv"
    readgenres(csvfile)
    readgenres2(csvfile2)

if __name__ == "__main__":
 main()