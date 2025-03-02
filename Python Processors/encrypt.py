import os
from cryptography.fernet import Fernet

base_directory = os.getenv("BASE_DIRECTORY", "D:\\Work\\AppHawk\\Test\\")
if not os.path.exists(base_directory):
    os.makedirs(base_directory)
    
key = Fernet.generate_key()

key_path = os.path.join(base_directory, "Vault\\secret.key")
with open(key_path, "wb") as key_file:
    key_file.write(key)

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Please set the OPENAI_API_KEY environment variable.")
    exit(1)

cipher_suite = Fernet(key)
encrypted_api_key = cipher_suite.encrypt(openai_api_key.encode())

encrypted_key_path = os.path.join(base_directory, "vault\\encrypted_openai_key.txt")
with open(encrypted_key_path, "wb") as file:
    file.write(encrypted_api_key)

print(f"Encryption successful. Your API key has been encrypted and saved to {encrypted_key_path}.")
