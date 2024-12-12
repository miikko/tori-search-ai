import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv('./state/.env')

AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
STATE_SERVER_USERNAME = os.getenv("STATE_SERVER_USERNAME")
STATE_SERVER_PASSWORD = os.getenv("STATE_SERVER_PASSWORD")

if AZURE_SUBSCRIPTION_ID is None or STATE_SERVER_USERNAME is None or STATE_SERVER_PASSWORD is None:
    raise Exception("AZURE_SUBSCRIPTION_ID, STATE_SERVER_USERNAME, and STATE_SERVER_PASSWORD must be set")
