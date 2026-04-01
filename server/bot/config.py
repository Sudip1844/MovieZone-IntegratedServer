# IntegratedServer/bot/config.py
# Bot configuration - copied from Tgbot/config.py with integrated changes

import os
import sys

# Add parent dir for config access
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Telegram Bot Configuration ---
BOT_TOKEN = os.getenv('BOT_TOKEN', '7269265854:AAFYz0-nIJVQbNcJTE1tiW5Nz6Zk-MnGfFA')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'movierecivebot')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'moviezone969')

# --- Owner Configuration ---
OWNER_ID = int(os.getenv('OWNER_ID', '5379553841'))

# --- Bot Settings ---
# Categories for movie addition (used by website now, kept for reference)
ADMIN_CATEGORIES = [
    "Bollywood 🇮🇳", "Hollywood 🇺🇸", "South Indian 🎬", "Web Series 🎥",
    "Bengali ✨", "Anime & cartoon 🌀", "Comedy 🤣", "Action 💥",
    "Romance 💑", "Horror 😱", "Thriller 🔍", "Sci-Fi 🛸",
    "K-Drama 🎎", "18+ 🔞", "Mystery 😲", "Marathi Movie 💟",
    "Punjabi Movie 🌠", "Gujarati Movie 🌄", "Crime 🚔", "Fantasy 🧿",
    "Adventure 🗺️", "Documentary 📚", "Drama 🎭"
]

BROWSE_CATEGORIES = [
    "All 🌐", "Bollywood 🇮🇳", "Hollywood 🇺🇸", "South Indian 🎬", "Web Series 🎥",
    "Bengali ✨", "Anime & cartoon 🌀", "Comedy 🤣", "Action 💥",
    "Romance 💑", "Horror 😱", "Thriller 🔍", "Sci-Fi 🛸",
    "K-Drama 🎎", "18+ 🔞", "Mystery 😲", "Marathi Movie 💟",
    "Punjabi Movie 🌠", "Gujarati Movie 🌄", "Crime 🚔", "Fantasy 🧿",
    "Adventure 🗺️", "Documentary 📚", "Drama 🎭"
]

CATEGORIES = ADMIN_CATEGORIES

LANGUAGES = [
    "Bengali", "Hindi", "English", "Tamil", "Telugu", "Korean", "Gujarati",
    "Malayalam", "Chinese", "Punjabi", "Marathi"
]

CONVERSATION_TIMEOUT = 600  # 10 minutes

# Post templates
SINGLE_MOVIE_POST_TEMPLATE = """
🍿 <b>{title}</b>

📌 <b>Language:</b> {languages}
☘️ <b>Genre:</b> {categories}
🗓️ <b>Release Year:</b> {release_year}
⏰ <b>Runtime:</b> {runtime}
⭐️ <b>IMDb Rating:</b> {imdb_rating}/10

🔗 <b>Download Link Below</b>
{download_links}

🔥 <b>Ultra Fast • Direct Access</b>
🛰️ <b>Join Now:</b> @{channel_username}
🔔 <b>New Movies Uploaded Daily!</b>
"""

SERIES_POST_TEMPLATE = """
📺 <b>{title}</b>

📌 <b>Language:</b> {languages}
☘️ <b>Genre:</b> {categories}
🗓️ <b>Release Year:</b> {release_year}
⏰ <b>Runtime:</b> {runtime}
⭐️ <b>IMDb Rating:</b> {imdb_rating}/10

<b>Available Episode - (Total ep)</b>
🔗 <b>Download Link Below</b>
{download_links}

🔥 <b>Ultra Fast • Direct Access</b>
🛰️ <b>Join Now:</b> @{channel_username}
🔔 <b>New Movies Uploaded Daily!</b>
"""