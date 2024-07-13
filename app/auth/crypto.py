from passlib.context import CryptContext
import base64
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def generate_random_base64_string(length: int):
  """Generates a random string of the specified length and encodes it in base64 (URL-safe).

  Args:
      length: The desired length of the random string (in bytes).

  Returns:
      A string containing the random data encoded in base64 (URL-safe).
  """
  # Generate random bytes using os.urandom()
  random_bytes = os.urandom(length)

  # Encode the random bytes in base64 (URL-safe) format
  encoded_string = base64.urlsafe_b64encode(random_bytes).decode()

  # Remove trailing newline character (optional)
  return encoded_string.rstrip("\n")