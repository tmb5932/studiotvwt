# Studio TVWT - Movies Database CLI

## Overview
Studio TVWT is a command-line interface (CLI) designed to interact with a PostgreSQL-based movies database. The project allows users to manage movies, rate them, create collections, follow users, track watch history, and receive personalized recommendations based on play history and community trends.

## Features
- User authentication (login, logout, account creation)
- Movie searching and viewing details
- Movie collection management (create, rename, delete, add, remove movies)
- User interaction (follow/unfollow users, view watch history)
- Rating and reviewing movies
- Watch history tracking
- Personalized movie recommendations
- User passwords salted and hashed before storing
- Data stored securely in a PostgreSQL database

## Installation
  
### Setup
1. Clone this repository:
   ```sh
   git clone https://github.com/tmb5932/studio-tvwt.git
   cd studio-tvwt
   ```
2. Configure environment variables:
   - Create a `.env` file in the project root and add the following:
     ```sh
     DB_USERNAME=your_username
     DB_PASSWORD=your_password
     SALT=your_salt_value
     ```
3. Run the application:
   ```sh
   python main.py
   ```

## Usage
### Commands Overview
| Command | Description |
|---------|-------------|
| HELP | Display available commands |
| CREATE ACCOUNT | Register a new user |
| LOGIN | Sign into an existing account |
| LOGOUT | Sign out from the current session |
| PROFILE | View profile details |
| CREATE COLLECTION | Create a new movie collection |
| LIST COLLECTIONS | View all user collections |
| RENAME COLLECTION | Rename an existing collection |
| DELETE COLLECTION | Remove a collection |
| SEARCH MOVIES | Find movies based on criteria |
| ADD TO COLLECTION | Add a movie to a collection |
| REMOVE FROM COLLECTION | Remove a movie from a collection |
| VIEW COLLECTION | View your or another user’s collection |
| FOLLOW | Follow another user |
| UNFOLLOW | Unfollow a user |
| SEARCH USERS | Search for other users |
| RATE MOVIE | Rate a movie |
| WATCH | Mark a movie or collection as watched |
| WATCH HISTORY | View watched movies |
| RECOMMEND | Get personalized movie recommendations |
| QUIT/EXIT | Exit the program |

### Example Usage
#### Creating an Account
```sh
Enter a command or type HELP: CREATE ACCOUNT
Enter your Email: user@example.com
Enter a username: myUsername
Enter a password: ********
Enter your first name: John
Enter your last name: Doe
Account created successfully!
```

#### Searching for a Movie
```sh
Enter a command or type HELP: SEARCH MOVIES
Enter the Movie's Title: Inception
Enter the Release Year: 2010
Sorting by: Rating DESC
Results:
1. Inception (2010) - 4.8 Stars
```

#### Viewing a Collection
```sh
Enter a command or type HELP: VIEW COLLECTION
Do you want to see your collections (Y) or another user's (N)? Y
Your collections:
1. Sci-Fi Favorites (5 movies, 12 hours runtime)
2. Oscar Winners (7 movies, 15 hours runtime)
```

## Database Schema
### Entities & Relations
- **User**: Stores user credentials, profile details, and interactions
- **Movie**: Stores movie metadata including title, runtime, rating, etc.
- **Genre**: Classifies movies by genre
- **ProductionTeam**: Stores directors, actors, and other key production staff
- **Studio**: Stores production studios
- **Collection**: Stores user-created movie lists
- **Platform**: Stores streaming platforms
- **UserFollows**: Handles user relationships (followers/following)
- **UserRates**: Stores movie ratings from users
- **UserWatches**: Tracks watch history

## Security Measures
- Passwords are hashed using SHA-256
- Secure SSH tunneling for database connection
- Parameterized queries to prevent SQL injection

## Contributors
- **Travis Brown** (tmb5932@rit.edu)
- **Vladislav Usatii** (vau3677@rit.edu)
- **William Walker** (wbw1991@rit.edu)
- **Timothy Sturges** (tos3454@rit.edu)

## License
This project is licensed under the MIT License.
---
For any issues or contributions, please open an issue or submit a pull request.

