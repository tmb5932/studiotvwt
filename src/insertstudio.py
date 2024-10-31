import os
import csv
import time
import psycopg2
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

def main():
    with open("companies.csv") as file:
        csv_reader = csv.reader(file)
        header = True
        studioid = 0;
        for row in csv_reader:
            if header:
                header = False
                continue
            title = row[0]
            sql_statement = "INSERT INTO studio (studioid, name) VALUES (" + str(studioid) + ", '" + title + "')"
            print(sql_statement)
            studioid = studioid + 1



if __name__ == "__main__":
    main()