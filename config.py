import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "TOKEN": os.getenv("DISCORD_TOKEN"),
    "ADMIN_ID": int(os.getenv("ADMIN_ID")),
    "TARGET_CHANNEL": int(os.getenv("TARGET_CHANNEL_ID")),
    "EXCLUDE_USERS": [
        int(os.getenv("EXCLUDE_USER1")),
        int(os.getenv("EXCLUDE_USER2"))
    ]
}