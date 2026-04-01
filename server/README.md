# IntegratedServer/README.md

# MovieZone Integrated Server

একটি একীভূত Python সার্ভার যা **Telegram Bot** এবং **Web API** উভয়ই চালায়।

## 🎯 বৈশিষ্ট্য

- ✅ **Telegram Bot**: মুভি ডাউনলোড লিংক শেয়ারিং
- ✅ **Web Server** (Flask): API এন্ডপয়েন্ট
- ✅ **Redirect Page**: বিজ্ঞাপন দেখানোর পর অরিজিনাল লিংকে রিডাইরেক্ট
- ✅ **Database**: Supabase PostgreSQL
- ✅ **Frontend**: React (আলাদা পোর্টে)

## 📦 প্রযুক্তি স্ট্যাক

- **Backend**: Python + Flask
- **Database**: Supabase (PostgreSQL)
- **Bot**: python-telegram-bot
- **ORM**: SQLAlchemy
- **Frontend**: React + Vite (separate port)

## 🚀 দ্রুত শুরু

### 1. পরিবেশ সেটআপ

```bash
cd IntegratedServer

# Python virtual environment তৈরি করুন
python -m venv venv
.\venv\Scripts\activate  # Windows

# Dependencies install করুন
pip install -r requirements.txt
```

### 2. Configuration

```bash
# .env.example থেকে .env তৈরি করুন
copy .env.example .env

# .env ফাইল এডিট করুন এবং Supabase credentials ভরুন
```

**Supabase Details দরকার:**

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DB_PASSWORD`

### 3. ডাটাবেস সেটআপ

```bash
# Supabase Dashboard → SQL Editor → .env.example আপলোড করুন
# SQL চালান এবং টেবিল তৈরি করুন
```

### 4. সার্ভার চালান

```bash
python main.py
```

**আউটপুট:**

```
╔═══════════════════════════════════════════════════════════╗
║         MovieZone - Integrated Server                     ║
║     Telegram Bot + Web Server (Unified Python)            ║
╚═══════════════════════════════════════════════════════════╝

🚀 Starting MovieZone Integrated Server...
🌐 Flask Server: http://0.0.0.0:5000
📊 Access API at: http://localhost:5000/api
🎬 Frontend will be at: http://localhost:5000
```

## 📡 API এন্ডপয়েন্ট

### স্বাস্থ্য চেক

```
GET /api/health
```

### মুভি লিংক

```
GET /api/movies
POST /api/movies
GET /api/movies/:shortId
```

### শর্ট লিংক

```
GET /api/shorts
POST /api/shorts
```

### Redirect

```
GET /api/redirect/:shortId
```

## 🤖 Telegram বট

বট স্বয়ংক্রিয়ভাবে background-এ চলবে যখন সার্ভার শুরু হয়।

### Features:

- `/start` - বটকে অ্যাক্টিভ করুন
- মুভি যোগ করুন (মালিক শুধু)
- শর্ট লিংক তৈরি করুন
- চ্যানেলে পোস্ট করুন

## 📁 ফোল্ডার কাঠামো

```
IntegratedServer/
├── main.py              # এন্ট্রি পয়েন্ট
├── config.py            # সেন্ট্রালাইজড কনফিগ
├── requirements.txt     # Dependencies
├── .env                 # গোপন কনফিগ (গিট-এ না)
├── bot/                 # Telegram Bot মডিউল
│   ├── bot_main.py
│   └── handlers/        # Bot হ্যান্ডলার
├── server/              # Flask ওয়েব সার্ভার
│   ├── app.py          # Flask অ্যাপ
│   └── routes/         # API রুট
├── database/            # ডাটাবেস লেয়ার
│   ├── models.py       # SQLAlchemy মডেল
│   └── connection.py   # DB সংযোগ
└── static/              # React বিল্ড (আউটপুট)
```

## 🔐 নিরাপত্তা

- ⚠️ **কখনো commit করবেন না** `.env` ফাইল
- ⚠️ **Service Role Key** গোপনীয় রাখুন
- ✅ `.gitignore`-এ `.env` যোগ করা আছে

## 🛠️ ডেভেলপমেন্ট

### Hot Reload চালু করুন

```bash
FLASK_ENV=development python main.py
```

### ডাটাবেস টেবিল পুনরায় সেটআপ করুন

```python
from database import init_db
init_db()
```

### SQL Queries ডিবাগ করুন

`config.py`-তে `echo=True` করুন

## 📝 TODO

- [ ] Telegram Bot handlers integrate করুন
- [ ] API routes implement করুন
- [ ] React frontend build সার্ভ করুন
- [ ] Authentication implement করুন
- [ ] Redirect page logic যোগ করুন
- [ ] Ad timer system implement করুন
- [ ] Error handling improve করুন

## 📞 সাপোর্ট

সমস্যা হলে:

1. `.env` সেটিংস চেক করুন
2. Supabase connection verify করুন
3. ডাটাবেস টেবিল exist করছে কিনা দেখুন
4. Logs দেখুন

---

**Version**: 1.0.0  
**Status**: 🚧 Under Development
