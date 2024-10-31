# Movie DB

To clone:

```
git clone <url_here>
cd studiotvwt/src
```

To generate a salt:

```
import os
os.urandom(16).hex() # copy and paste as SALT= into .env
```

To successfully login, you must edit .env_example to include your correct db username and password. Then rename .env_example to .env.

To make an account:

```
python3 src/main.py --create-account EMAIL PASSWORD USERNAME
```

## GET

* table
* col='*'
* criteria = None

## POST

* table
* data

## Methods

Capital letters specify what value is expected to query the database.

```
--create-account EMAIL PASSWORD USERNAME FIRST LAST
--login EMAIL PASSWORD
--create-collection COLLECTION
--list-collections USERNAME
--search-movies QUERY CRITERIA
--add-movie COLLECTION MOVIE
--delete-collection COLLECTION
--follow USERNAME
--unfollow USERNAME
--terminate
```

---

Documentation written by Vladislav Usatii (vau3677@rit.edu)
