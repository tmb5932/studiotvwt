import sys, os, binascii, hashlib
from dotenv import load_dotenv

""" SHA 256 Hash """
def encode_password(password):
	load_dotenv()
	salt = os.getenv("SALT")

	salt_bytes = bytes.fromhex(salt)
	password_bytes = password.encode('utf-8')

	hash_value = hashlib.sha3_256(salt_bytes + password_bytes)
	return hash_value.hexdigest()

def valid_password(password_hash, guess):
	return encode_password(guess) == password_hash
