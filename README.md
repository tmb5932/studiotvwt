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
