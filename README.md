# The Christmas Boutique — Django E-commerce Site

Your static HTML/CSS "Christmas Boutique" site rebuilt as a full **Django + SQL**
web app, with JavaScript for interactivity. All your original pages
(Home, Shop All, Ornaments, Trees, Lights, Contact) are now dynamic and
backed by a real database.

## What was added

| Layer | What |
|---|---|
| **Python / Django** | Full MVC app: models, views, forms, URL routing, admin panel |
| **SQL (via Django ORM, SQLite by default)** | `Category`, `Product`, `Order`, `OrderItem`, `ContactMessage`, `Newsletter` tables |
| **JavaScript** | AJAX "Add to Cart" (no page reload), live cart badge, quantity steppers, client-side form validation |
| **New features** | Shopping cart (session-based), checkout → real orders, product detail pages, search + sort on shop pages, contact form saved to DB, newsletter signup, user register/login/logout, order history for logged-in users, Django admin to manage everything |

## Project layout

```
christmas_boutique/
├── manage.py
├── requirements.txt
├── ecom_project/          # Django project settings/urls
├── shop/                  # The main app
│   ├── models.py          # SQL tables (Category, Product, Order, ...)
│   ├── views.py           # Page logic
│   ├── forms.py           # Contact / checkout / register forms
│   ├── cart.py            # Session-based shopping cart
│   ├── urls.py
│   ├── admin.py           # Admin panel registration
│   ├── management/commands/seed_data.py   # Loads your original products
│   └── templates/shop/    # All pages (base, home, shop, cart, checkout, ...)
└── static/shop/
    ├── css/ (web.css + site.css)
    └── js/main.js
```

## Run it locally

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure local environment variables (PowerShell)
$env:SECRET_KEY = & .\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
$env:DEBUG = 'True'
$env:ALLOWED_HOSTS = 'localhost,127.0.0.1,testserver'

# 4. Set up the database (creates db.sqlite3 with all tables)
python manage.py migrate

# 5. Load your original products (Trees, Lights, Ornaments) into the DB
python manage.py seed_data

# 6. Create an admin account
python manage.py createsuperuser

# 7. Run the server
python manage.py runserver
```

The deployment environment must provide `SECRET_KEY`, `DEBUG`, and
`ALLOWED_HOSTS`. `.env.example` documents their expected format; Django does
not load `.env` files automatically.

Then open:
- **http://127.0.0.1:8000/** — the storefront
- **http://127.0.0.1:8000/admin/** — manage products, categories, orders,
  contact messages, and newsletter signups (login with the superuser you
  created)

## Using a "real" SQL database instead of SQLite

SQLite (a single `db.sqlite3` file) is used by default so it runs anywhere
with zero setup. To switch to MySQL or PostgreSQL for production, edit
`ecom_project/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',   # or mysql
        'NAME': 'christmas_boutique',
        'USER': 'youruser',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```
Then install the driver (`psycopg2-binary` for Postgres, `mysqlclient` for
MySQL) and re-run `python manage.py migrate`.

## Adding more products/categories

Easiest way: go to `/admin/`, log in, and add Categories/Products there —
no code needed. Or extend `shop/management/commands/seed_data.py` and
re-run `python manage.py seed_data`.

## Design

The site now has its own visual identity instead of the original red/white
Wix look:

- **Palette**: deep pine green, cranberry red, antique gold, soft cream
- **Type**: Fraunces (serif, headings) + Work Sans (body/UI), loaded from Google Fonts
- **Motion**: a quiet falling-snow animation in the hero (canvas, pauses if the
  visitor has "reduce motion" turned on), sections fade/slide in once as you
  scroll, product images zoom gently on hover, and the cart icon bumps when
  something is added — nothing more, so it stays fast and uncluttered
- All of this lives in `static/shop/css/site.css` and `static/shop/js/main.js`
  if you want to adjust colors, fonts, or animation timing

Re-run `python manage.py collectstatic` only when deploying; it's not needed
for local development.

## Next steps you could add

- Real payment gateway (Stripe/Razorpay) at checkout instead of a plain order form
- Product image upload (currently uses external image URLs, like your original site)
- Order status emails (the email backend is already wired to console output in dev)
- Product reviews/ratings model
- Wishlist model
- REST API (Django REST Framework) if you want a separate JS/React front-end later
