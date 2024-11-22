import os

import numpy as np
import psycopg2
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

# Get data
def fetch_data(query):
    """
    Fetch data from the database using an SSH tunnel and return as a DataFrame.
    """
    load_dotenv()
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    dbName = "p320_11"

    with SSHTunnelForwarder(
        ('starbug.cs.rit.edu', 22),
        ssh_username=username,
        ssh_password=password,
        remote_bind_address=('127.0.0.1', 5432)
    ) as server:
        server.start()
        print("SSH tunnel established")

        params = {
            'database': dbName,
            'user': username,
            'password': password,
            'host': 'localhost',
            'port': server.local_bind_port
        }

        with psycopg2.connect(**params) as conn:
            with conn.cursor() as curs:
                print("Database connection established")
                curs.execute(query)
                results = curs.fetchall()

    return results

# Plot bubble chart
def plot_bubble_chart(data_values):
    # Normalize bubble size
    data_values['Bubble Size'] = 100

    # Create a custom colormap with red to orange to green
    custom_cmap = LinearSegmentedColormap.from_list(
        "RedOrangeGreen", ["red", "orange", "green"]
    )

    # Normalize ratings for color mapping
    normalized_ratings = (data_values['Average Rating'] - data_values['Average Rating'].min()) / \
                         (data_values['Average Rating'].max() - data_values['Average Rating'].min())
    colors = custom_cmap(normalized_ratings)  # Apply colormap

    # Identify top 3 for highest average rating (y-axis), movies directed (x-axis), and lowest y-axis
    top_y = data_values.nlargest(3, 'Average Rating')  # Top 3 highest ratings
    low_y = data_values.nsmallest(2, 'Average Rating')  # Lowest 2 ratings
    top_x = data_values.nlargest(5, 'Movies Directed')  # Top 3 most movies directed
    to_label = pd.concat([top_y, low_y, top_x]).drop_duplicates()

    # Create the figure and axes
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
    scatter = ax.scatter(
        data_values['Movies Directed'], data_values['Average Rating'],
        s=data_values['Bubble Size'], c=colors, alpha=0.85, edgecolors="k", linewidth=0.5, label="Directors"
    )

    # Add a trend line
    x = data_values['Movies Directed']
    y = data_values['Average Rating']
    z = np.polyfit(x, y, 1)  # Fit a linear regression line (degree=1)
    p = np.poly1d(z)

    # Extend the range of x for the trend line
    x_extended = np.linspace(x.min(), x.max() + 5, 40)  # Extend by 10 units on both sides
    ax.plot(x_extended, p(x_extended), "r--", label="Trend Line")  # Add the trend line to the plot

    # Add annotations for certain directors
    for i in to_label.index:
        ax.text(
            data_values['Movies Directed'][i], data_values['Average Rating'][i] + 0.03,
            f"{data_values['Director Name'][i]}", fontsize=6, ha='center'
        )

    ax.set_title('Directors Average Rating & The Amount of Movies They Have Directed', fontsize=22, pad=10)
    ax.set_xlabel('Movies Directed', fontsize=19, labelpad=15)
    ax.set_ylabel('Average Rating', fontsize=19, labelpad=15)
    ax.legend()
    ax.grid(alpha=0.3)

    plt.show()

# Main script
if __name__ == "__main__":

    query = """
    SELECT
        d.firstname || ' ' || d.lastname AS director_name,
        COUNT(m.movieid) AS movies_directed,
        AVG(ur.rating) AS avg_rating
    FROM
        productionteam d
            JOIN
        moviedirects md ON d.productionid = md.productionid
            JOIN
        movie m ON md.movieid = m.movieid
            LEFT JOIN
        userrates ur ON m.movieid = ur.movieid
    WHERE 
        d.productionid > 999
    GROUP BY
        d.lastname, d.firstname
    ORDER BY
        avg_rating DESC
    """

    try:
        # Get data
        results = fetch_data(query)

        # Arrange it
        data = {
            'Director Name': [row[0] for row in results],
            'Movies Directed': [row[1] for row in results],
            'Average Rating': [float(row[2]) for row in results],
        }

        df = pd.DataFrame(data)

        # Plot chart
        plot_bubble_chart(df)
    except Exception as e:
        print(f"Error: {e}")