import re
import os

bot_dir = r"d:\Antigravity\New folder\MovieZone-IntegratedServer\server\bot"

# 1. movie_handlers.py
mh_path = os.path.join(bot_dir, "handlers", "movie_handlers.py")
with open(mh_path, 'r', encoding='utf-8') as f:
    mh = f.read()

mh = mh.replace('REQUEST_MOVIE_NAME, DELETE_MOVIE_NAME, SHOW_STATS_MOVIE_NAME, SHOW_STATS_OPTION, SHOW_STATS_CATEGORY, SHOW_STATS_ADMIN, SHOW_STATS_MOVIE_LIST = range(7)', 'REQUEST_MOVIE_NAME = range(1)')
mh = re.sub(r'# --- Remove Movie \(Owner Only\) ---.*?async def cancel_movie_conversation', 'async def cancel_movie_conversation', mh, flags=re.DOTALL)
mh = re.sub(r'remove_movie_conv = ConversationHandler.*?# Main handler list to be imported', '# Main handler list to be imported', mh, flags=re.DOTALL)
mh = mh.replace('    remove_movie_conv,\n', '')
mh = mh.replace('"🗑️ Remove Movie", ', '')
with open(mh_path, 'w', encoding='utf-8') as f:
    f.write(mh)

# 2. bot_main.py
bm_path = os.path.join(bot_dir, "bot_main.py")
with open(bm_path, 'r', encoding='utf-8') as f:
    bm = f.read()

bm = bm.replace(', remove_movie_conv', '')
bm = bm.replace('    application.add_handler(remove_movie_conv)\n', '')
bm = bm.replace(' & ~filters.Regex("^🗑️ Remove Movie$")', '')
with open(bm_path, 'w', encoding='utf-8') as f:
    f.write(bm)

# 3. callback_handler.py
ch_path = os.path.join(bot_dir, "handlers", "callback_handler.py")
with open(ch_path, 'r', encoding='utf-8') as f:
    ch = f.read()

ch = re.sub(r'\s*elif callback_data in \[\'confirm_delete\'.*?return\n', '\n', ch, flags=re.DOTALL)
with open(ch_path, 'w', encoding='utf-8') as f:
    f.write(ch)

# 4. utils.py
utils_path = os.path.join(bot_dir, "utils.py")
with open(utils_path, 'r', encoding='utf-8') as f:
    ut = f.read()

ut = ut.replace(', KeyboardButton("🗑️ Remove Movie")', '')
with open(utils_path, 'w', encoding='utf-8') as f:
    f.write(ut)

print("Cleanup script complete.")
