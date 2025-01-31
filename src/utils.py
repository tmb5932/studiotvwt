import os, hashlib
from dotenv import load_dotenv

# month constants for verbose output
MONTHS = {
	1: "January",
	2: "February",
	3: "March",
	4: "April",
	5: "May",
	6: "June",
	7: "July",
	8: "August",
	9: "September",
	10: "October",
	11: "November",
	12: "December"
}

""" SHA 256 Hash """
def encode_password(password):
	load_dotenv()
	salt = os.getenv("SALT")

	salt_bytes = bytes.fromhex(salt)
	password_bytes = password.encode('utf-8')

	hash_value = hashlib.sha3_256(salt_bytes + password_bytes)
	return hash_value.hexdigest()[:50]

def valid_password(password_hash, guess):
	return encode_password(guess) == password_hash

""" Colors """
class Color:
	colors = {
		"red": "\033[31m",
		"green": "\033[32m",
		"yellow": "\033[33m",
		"blue": "\033[34m",
		"reset": "\033[0m"
	}

	def __init__(self, color: str):
		self.start = Color.colors.get(color.lower(), Color.colors["reset"])
		self.end = Color.colors["reset"]

	def apply(self, text: str) -> str:
		return f"{self.start}{text}{self.end}"

red, green, yellow, blue = Color("red"), Color("green"), Color("yellow"), Color("blue")
