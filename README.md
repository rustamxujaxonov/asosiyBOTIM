# Tanishuvlar BOT — Anonim Tanishuvlar Telegram Boti

Professional, "Dispatcher/Router" arxitekturasida qurilgan, PostgreSQL (asyncpg + SQLAlchemy async) bilan ishlaydigan anonim tanishuvlar boti.

## 📁 Loyiha strukturasi

```
tanishuvlar_bot/
├── bot.py                      # Kirish nuqtasi (entry point)
├── config.py                   # .env / Railway Variables'ni yuklovchi konfiguratsiya
├── requirements.txt
├── Procfile                    # Railway uchun ishga tushirish komandasi
├── .env.example                # Namuna muhit o'zgaruvchilari
│
├── database/
│   ├── models.py                # SQLAlchemy ORM modellari (User, ActiveQueue, ActiveChat, PaymentRequest)
│   ├── engine.py                 # Async engine, session maker, jadval yaratish
│   └── requests/
│       ├── users.py              # Foydalanuvchi CRUD
│       ├── chat.py                # Navbat va suhbat CRUD
│       └── payments.py            # To'lov so'rovlari CRUD
│
├── handlers/
│   ├── start.py                  # /start komandasi
│   ├── subscription.py            # Obunani tekshirish
│   ├── registration.py            # Ro'yxatdan o'tish (FSM)
│   ├── settings.py                 # Profil sozlamalari (FSM)
│   ├── profile.py                   # Mening profilim
│   ├── search.py                     # Suhbatdosh qidirish
│   ├── chat_relay.py                  # Xabar almashish + suhbatni yakunlash
│   ├── premium_prompt.py               # Premium paketlar, referal
│   ├── payment_receipt.py               # Chek qabul qilish
│   ├── admin_approval.py                 # Admin tasdiqlash/rad etish
│   └── admin_stats.py                     # /stats (faqat admin)
│
├── keyboards/
│   ├── reply.py                   # Reply klaviaturalar
│   └── inline.py                   # Inline klaviaturalar + CallbackData
│
├── middlewares/
│   ├── db.py                       # AsyncSession inject qilish
│   ├── subscription.py              # Majburiy obuna tekshiruvi
│   └── throttling.py                 # Anti-flood
│
├── states/
│   └── states.py                    # FSM State guruhlari
│
└── filters/
    └── admin.py                      # IsAdmin filtri
```

## ⚙️ O'rnatish (lokal test uchun)

```bash
# 1. Virtual muhit yaratish
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 2. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 3. .env faylini sozlash
cp .env.example .env
# .env faylini oching va o'z qiymatlaringizni kiriting

# 4. Botni ishga tushirish
python bot.py
```

## 🚂 Railway'ga deploy qilish

1. **GitHub'ga yuklang**: Loyihani GitHub repositoriyaga push qiling.

2. **Railway'da yangi loyiha yarating**: "Deploy from GitHub repo" orqali repository'ni tanlang.

3. **PostgreSQL qo'shing**: Railway loyihasida "+ New" → "Database" → "Add PostgreSQL". Bu avtomatik `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` o'zgaruvchilarini yaratadi.

4. **Muhit o'zgaruvchilarini bog'lang**: Bot xizmatining "Variables" bo'limida quyidagilarni qo'shing:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
   - `ADMIN_GROUP_ID`
   - `CHANNEL_ID`
   - `CHANNEL_URL`
   - `BOT_USERNAME`
   - `CARD_NUMBER`
   - `CARD_OWNER`
   - PostgreSQL o'zgaruvchilarini esa "Reference Variable" tugmasi orqali PostgreSQL xizmatidan bog'lang (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`).

5. **Bot huquqlarini sozlang**:
   - Botni **kanalga admin** qilib qo'shing (majburiy obunani tekshirish uchun shart).
   - Botni **admin guruhiga** a'zo qiling (chek yuborish uchun).

6. **Deploy**: Railway avtomatik `Procfile`'dagi `python bot.py` komandasi orqali botni ishga tushiradi.

## 🔑 Muhim texnik eslatmalar

- **Anonimlik**: Xabarlar `bot.copy_message()` orqali yuboriladi — bu `forward_message()`'dan farqli o'laroq, asl jo'natuvchi ismini ko'rsatmaydi.
- **FSM Storage**: Hozircha `MemoryStorage` ishlatilgan (bitta server uchun yetarli). Agar Railway'da bot qayta ishga tushsa, foydalanuvchilar FSM holatini yo'qotadi — bu muammo emas, chunki ular shunchaki qayta tugma bosishlari kifoya.
- **Majburiy obuna**: Bot albatta kanalda **admin** bo'lishi kerak, aks holda `get_chat_member` xato qaytaradi.
- **Referal tizimi**: Bonus faqat foydalanuvchi **to'liq ro'yxatdan o'tgandan keyin** hisoblanadi (shunchaki botni ishga tushirish yetarli emas).
- **Premium stacking**: Agar foydalanuvchi Premium muddati tugamasdan yana paket sotib olsa, yangi kunlar mavjud muddatga **qo'shiladi** (ustma-ust yozilmaydi).

## 🗄️ Ma'lumotlar bazasi jadvallari

| Jadval | Vazifasi |
|---|---|
| `users` | Foydalanuvchi profili, Premium holati, referal statistikasi |
| `active_queue` | "Qidiruvda" turgan foydalanuvchilar navbati |
| `active_chats` | Hozirda faol bo'lgan (bog'langan) suhbat juftliklari |
| `payment_requests` | Yuborilgan cheklar va ularning holati (kutilmoqda/tasdiqlandi/rad etildi) |

Jadvallar bot birinchi marta ishga tushganda **avtomatik** yaratiladi (`create_db_and_tables`).
