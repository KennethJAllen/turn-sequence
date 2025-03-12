import os
from dotenv import load_dotenv

def main():
    load_dotenv()  # loads variables from .env

    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    print(maps_api_key)


if __name__ == "__main__":
    main()

