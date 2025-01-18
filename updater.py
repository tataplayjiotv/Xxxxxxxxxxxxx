import subprocess
from urllib3 import disable_warnings
from Crypto.Cipher import AES
from time import sleep
import requests
import logging
import base64
import json

disable_warnings()
logging.basicConfig(level=logging.DEBUG)

def decrypt_source_url(encrypted_data):
    SECRET_KEY = "aesEncryptionKey".encode()
    cipher = AES.new(SECRET_KEY, AES.MODE_ECB)
    decrypted = cipher.decrypt(base64.b64decode(encrypted_data[:-3]))
    padding_length = decrypted[-1]
    decrypted = decrypted[:-padding_length]
    return decrypted.decode('utf-8')

session = requests.Session()
session.verify = False
session.trust_env = False
session.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Authorization": "bearer zTVewm2eYqS7gNF0AWvDfesNkD1CerLq",
}

def git_commit_and_push():
    try:
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions"], check=True)

        subprocess.run(["git", "add", "origin.json"], check=True)
        subprocess.run(["git", "commit", "-m", "Updated via Script 🤖"], check=True)
        subprocess.run(["git", "push"], check=True)
        logging.info("Changes committed and pushed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Git command failed: {e}")
        logging.debug(f"Command output: {e.output}")


def generate_origin():
    init_source_response = session.get("https://tm.tapi.videoready.tv/portal-search/pub/api/v1/channels?limit=1000&ott=true")
    init_origin_data = init_source_response.json()["data"]["list"]

    origin_data = init_origin_data.copy()

    for index, origin_channel_data in enumerate(init_origin_data):
        for _ in range(3):
            origin_channel_id = origin_channel_data["id"]
            source_response = session.get(f"https://tm.tapi.videoready.tv/digital-feed-services/api/partner/cdn/player/details/LIVE/{origin_channel_id}")

            if source_response.status_code != 200:
                sleep(10)
                continue

            source_data = source_response.json()["data"]
            origin_source_data = {}

            for key, value in source_data.items():
                if "#v2" in str(value):
                    origin_source_data[key] = decrypt_source_url(value)

            origin_channel_data["streamData"] = origin_source_data
            origin_data[index] = origin_channel_data

            with open("origin.json", "w") as file:
                json.dump(origin_data, file, indent=4)

            if index != 0 and index % 70 == 0:
                git_commit_and_push()

            break

        sleep(5)

if __name__ == "__main__":
    generate_origin()
