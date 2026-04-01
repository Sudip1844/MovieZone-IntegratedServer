# MovieZone - Integrated Server

এই প্রজেক্টটি একটি **Full-stack Web Server এবং Telegram Bot** এর সমন্বয়ে তৈরি করা হয়েছে, যা মূলত মুভি শেয়ারিং এবং লিংক ম্যানেজমেন্টের জন্য ব্যবহৃত হয়।

## 🎯 বৈশিষ্ট্য (Features)

- ✅ **Telegram Bot**: মুভি ডাউনলোড লিংক শেয়ারিং, সার্চ, এবং অ্যাডমিনিস্ট্রেশন।
- ✅ **Web Server** (Flask): API এন্ডপয়েন্ট (Movies, Redirects, Shorts)।
- ✅ **Redirect Page**: বিজ্ঞাপন (ad page) দেখানোর পর অরিজিনাল লিংকে রিডাইরেক্ট করে।
- ✅ **Database**: Supabase PostgreSQL সার্ভার।
- ✅ **Frontend**: React/Vanilla HTML (static ফোল্ডার থেকে সার্ভ করা)।

## 📦 প্রযুক্তি স্ট্যাক (Tech Stack)

- **Backend**: Python, Flask
- **Database**: Supabase (PostgreSQL)
- **Bot**: python-telegram-bot
- **ORM**: SQLAlchemy
- **Frontend**: HTML/CSS/JS (Served from `static/`)

## 📁 ফোল্ডার স্ট্রাকচার

```
MovieZone-IntegratedServer/
├── server/              # Flask সার্ভার এবং টেলিগ্রাম বট
│   ├── main.py          # এন্ট্রি পয়েন্ট
│   ├── config.py        # কনফিগ ফাইল
│   ├── requirements.txt # ডিপেন্ডেন্সি
│   ├── .env             # সিক্রেট পরিবেশ চলক (git-এ ইগনোর করা)
│   ├── bot/             # টেলিগ্রাম বট মডিউল
│   ├── routes/          # Flask API রুটস
│   └── database/        # ডাটাবেস লেয়ার (Supabase)
├── static/              # ফ্রন্টএন্ড এর HTML/CSS/JS ফাইল
│   ├── admin.html       # অ্যাডমিন প্যানেল
│   ├── owner.html       # ওনার প্যানেল
│   ├── ad_page.html     # রিডাইরেক্ট পেজ (Ad page)
│   └── index.html       # হোমপেজ
└── README.md            # প্রজেক্ট ডকুমেন্টেশন
```

## 🚀 কিভাবে রান করবেন?

### ১. পরিবেশ সেটআপ
```bash
# Python virtual environment তৈরি করুন (ঐচ্ছিক কিন্তু রিকমেন্ডেড)
python -m venv venv
.\venv\Scripts\activate  # Windows-এর জন্য

# Dependencies install করুন
pip install -r server/requirements.txt
```

### ২. Configuration (.env)
আপনার `server/` ফোল্ডারে একটি `.env` ফাইল থাকতে হবে। તેમાં নিচের Supabase এবং Bot Credentials থাকতে হবে:
- `BOT_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DB_PASSWORD`

### ৩. ডাটাবেস সেটআপ
প্রথমে `server/SUPABASE_SQL_SCHEMA.sql` এর স্কিমাগুলো Supabase Dashboard এর SQL Editor এ রান করে টেবিলগুলো তৈরি করে নিন। 

### ৪. সার্ভার এবং বট স্টার্ট
```bash
python server/main.py
```
সার্ভার সফলভাবে চালু হলে আপনি নিচের লিংকগুলোতে অ্যাক্সেস করতে পারবেন:
- 🌐 Home: `http://localhost:5000`
- 🖥️ Admin: `http://localhost:5000/admin`
- 👑 Owner: `http://localhost:5000/sudip`

## 📡 API এন্ডপয়েন্ট

- `GET /api/health` - সার্ভারের স্ট্যাটাস চেক
- `GET /api/movies`, `POST /api/movies` - মুভি ম্যানেজমেন্ট
- `GET /api/shorts`, `POST /api/shorts` - শর্ট লিংক
- `GET /api/redirect/:shortId` - রিডাইরেক্ট মেকানিজম

## 🔐 নিরাপত্তা
- ⚠️ **কখনোই** `.env` ফাইল গিটহাবে পুশ করবেন না (ইতিমধ্যেই ইগনোর করা আছে)।
- ⚠️ Service Role Key গোপনীয় রাখুন।
