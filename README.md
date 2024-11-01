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

## Methods

Capital letters specify what value is expected to query the database.

```
# working
--create-account EMAIL PASSWORD USERNAME FIRST LAST
--login EMAIL PASSWORD

# working
--create-collection COLLECTION
--edit-collection COLLECTION NEWNAME
--list-collections USERNAME # not working
--delete-collection COLLECTION

# not working
--search-movies QUERY CRITERIA
--add-movie COLLECTION MOVIE
--delete-movie COLLECTION MOVIE

# working
--follow USERNAME
--unfollow USERNAME

# working
--terminate
```

---

Documentation written by Vladislav Usatii (vau3677@rit.edu)
