import sys, os
import argparse
import ast
import csv
from _csv import reader
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import psycopg2


GENRESLIST = []


# Insert genres function IMDB MOVIE DATA CSV
# inserts a bunch of genres and genreid read and parsed from the csv into datagrips genre table.
# params: csvfile ( IMDB-MOVIE-DATA.csv )
def readgenres(csvfile):

    # list of unique genres and the start of the genreid
    global GENRESLIST


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





# Insert genres functionmovies_metadata.csv
# Inserts a bunch of genres and genreid read and parsed from the csv into datagrips genre table.
# params: csvfile (movies_metadata.csv)
def readgenres2(csvfile):

    global GENRESLIST


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






def genre_read3(csvfile):
    global GENRESLIST
    with open(csvfile, encoding='utf-8') as c:
        csv_reader = csv.reader(c)
        header = True
        for row in csv_reader:
            if header:
                header = False
                continue
            genre = row[1].strip()
            if genre and genre not in GENRESLIST:
                GENRESLIST.append(genre)


def genre_read4(csvfile):
    global GENRESLIST
    with open(csvfile, encoding='utf-8') as c:
        csv_reader = csv.reader(c)
        header = True
        for row in csv_reader:
            if header:
                header = False
                continue
            genres_str = row[10]  # Assuming the genre column is at index 10
            col_genres = genres_str.split(", ")
            for genre in col_genres:
                new_genre = genre.strip()
                if new_genre and new_genre not in GENRESLIST:
                    GENRESLIST.append(new_genre)




# make an insert query with genreid and the name of the genre in genrelist
#calls executemany to execute all at the same time.
def insert_genres(curs, valuesArray):
    insert_query = """
    INSERT INTO genre (genreid, name) VALUES (%s, %s)
    """
    curs.executemany(insert_query, valuesArray)


# connect and then set a genre id to each in genreslist and then call insert genres
def ssh_insert_genres():
    try:
        #load_dotenv()
        username = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dbName = "p320_11"
        valuesArray = []
        with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                                ssh_username=username,
                                ssh_password=password,
                                remote_bind_address=('127.0.0.1', 5432)) as server:
            server.start()
            print("SSH tunnel established")

            params = {
                'database': dbName,
                'user': username,
                'password': password,
                'host': 'localhost',
                'port': server.local_bind_port
            }
            conn = psycopg2.connect(**params)
            curs = conn.cursor()
            print("Database connection established")

            csvfile = "IMDB-Movie-Data.csv"
            csvfile2 = "movies_metadata.csv"
            csvfile3 = "genremore.csv"
            csvfile4 = "netflix_titles.csv"
            readgenres(csvfile)
            readgenres2(csvfile2)
            genre_read3(csvfile3)
            genre_read4(csvfile4)

            #only insert the new generes from genreread3
            valuesArray = [(i + 44, genre) for i, genre in enumerate(GENRESLIST[43:])]
            insert_genres(curs, valuesArray)

            conn.commit()
            print("All genres inserted successfully!")
            conn.close()
    except:
        print("Connection failed")


if __name__ == "__main__":
    ssh_insert_genres()
