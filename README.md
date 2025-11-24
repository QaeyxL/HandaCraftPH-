# HandaCraftPH

## Project Tree

```
HandaCraftPH-
├─ .coverage
├─ client
│  └─ scripts
│     └─ dashboard.js
├─ handacraftph
│  └─ handacraftph
│     ├─ asgi.py
│     ├─ handacraftph
│     │  ├─ asgi.py
│     │  ├─ settings.py
│     │  ├─ urls.py
│     │  ├─ wsgi.py
│     │  └─ __init__.py
│     ├─ settings.py
│     ├─ urls.py
│     ├─ wsgi.py
│     └─ __init__.py
├─ hc_app
│  ├─ admin.py
│  ├─ apps.py
│  ├─ context_processors.py
│  ├─ forms.py
│  ├─ management
│  │  └─ commands
│  │     └─ geocode_profiles.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_category.py
│  │  ├─ 0003_cartitem.py
│  │  ├─ 0004_alter_product_category.py
│  │  ├─ 0005_alter_category_name.py
│  │  ├─ 0006_productimage.py
│  │  ├─ 0007_alter_productimage_image.py
│  │  ├─ 0008_remove_product_video_order_orderitem_userprofile.py
│  │  ├─ 0009_product_height_product_length_product_weight_and_more.py
│  │  ├─ 0010_alter_userprofile_city_and_more.py
│  │  ├─ 0011_order_shipping_label_url_order_tracking_code.py
│  │  ├─ 0012_product_stock.py
│  │  ├─ 0013_order_estimated_delivery.py
│  │  ├─ 0014_order_buyer_city_order_buyer_country_and_more.py
│  │  ├─ 0015_product_seller_city_product_seller_country_and_more.py
│  │  ├─ 0016_remove_order_shipping_label_url_and_more.py
│  │  ├─ 0017_quote.py
│  │  ├─ 0018_attribute_cartitem_customization_cartitem_item_price_and_more.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ products
│  │  └─ media
│  ├─ signals.py
│  ├─ static
│  │  └─ hc_app
│  │     ├─ dashboard.css
│  │     ├─ images
│  │     │  └─ logo.png
│  │     ├─ main.css
│  │     ├─ scripts
│  │     │  ├─ admin_dashboard.js
│  │     │  ├─ customizer.js
│  │     │  └─ dashboard.js
│  │     └─ vendor
│  │        └─ README.txt
│  ├─ templates
│  │  └─ hc_app
│  │     ├─ admin_dashboard.html
│  │     ├─ base.html
│  │     ├─ cart.html
│  │     ├─ catalog.html
│  │     ├─ categories.html
│  │     ├─ category_products.html
│  │     ├─ checkout.html
│  │     ├─ confirm_deactivate_account.html
│  │     ├─ confirm_delete_account.html
│  │     ├─ customize.html
│  │     ├─ dashboard.html
│  │     ├─ delete_confirmed.html
│  │     ├─ delete_request_sent.html
│  │     ├─ demo_setup.html
│  │     ├─ home.html
│  │     ├─ index.html
│  │     ├─ login.html
│  │     ├─ my_listings.html
│  │     ├─ my_orders.html
│  │     ├─ order_confirmation.html
│  │     ├─ password_change.html
│  │     ├─ password_change_done.html
│  │     ├─ product_detail.html
│  │     ├─ register.html
│  │     ├─ search_results.html
│  │     ├─ sell.html
│  │     └─ workflow_edit.html
│  ├─ templatetags
│  │  ├─ mul_filters.py
│  │  └─ __init__.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ ITMGT 45.03 - Group 3 GC2.pdf
├─ manage.py
├─ media
│  └─ products
│     └─ images
│        ├─ Screenshot_2025-03-13_223830.png
│        ├─ Screenshot_2025-10-13_224110.png
│        ├─ Screenshot_2025-10-13_230045.png
│        ├─ Screenshot_2025-11-05_005713.png
│        ├─ Screenshot_2025-11-05_013525.png
│        ├─ Screenshot_2025-11-10_092310.png
│        ├─ Screenshot_2025-11-12_031910.png
│        └─ Screenshot_2025-11-23_153907.png
├─ Procfile
├─ README.md
└─ requirements.txt

```
## HandaCraftPH Overview
HandaCraftPH is designed as a culturally conscious marketplace system that supports MSMEs and traditional artisans through customizable workflows and role-based access.

## Tech stack & version numbers.

| Component   | Platform | Justification | Version |
|-------------|-------------| --------------- | ----- |
| Front-End   | HTML (structure), CSS (visuals), and JS (interactivity)   | Fast load times, responsive design, and broad browser compatibility | |
| Back-End | Django | Secure, scalable, and comes with built-in tools for rapid development |5.2.8|
| Database | SQLite | Lightweight, fast, and ideal for small to medium-sized projects | 3.50.4| 
| External APIs / services | 1. Twilio</br> 2. Easypost API </br> 3. Quotable.io | | 1. 9.8.5 |

## Deployment link.
The live site is hosted on Render:  (https://handacraftph.onrender.com)

## Setup instructions.
1. To run HandaCraftPH locally:
<br>`git clone https://github.com/QaeyxL/HandaCraftPH-.git
cd HandaCraftPH-`
2. Create and activate a virtual environment
<br>`python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate`

3. Install dependencies
<br> `pip install -r requirements.txt`
4. Apply migrations
<br> `python manage.py makemigrations
<br>python manage.py migrate`
5. Run the development server
`python manage.py runserver`
6. Access the app
<br> Visit http://127.0.0.1:8000/ in your browser.

## API documentation & links.
### Twilio API
Used for sending SMS and WhatsApp notifications during registration and order confirmation.
[Twilio Docs](https://www.twilio.com/docs)

### Easypost API
Used for shipping and tracking packages across multiple carriers.
[Easypost API Docs](https://www.easypost.com/docs)

### Quotable.io API
Used to fetch random quotes for enhancing the login and registration pages.
[Quotable.io API](https://github.com/lukePeavey/quotable)

### Nominatim API
API uses OpenStreetMap data. This is used to verify and/or suggest addresses to the user.
[Nominatim API](https://nominatim.org/release-docs/latest/)

## List of Implemented Features
- **User Login**
  A user can be a seller and a buyer without needing separate accounts for it. They must make an account to access HandaCraftPH. 

- **Catalog and Search**
  Products are filtered by their category. If a user wishes to search for a specific product, they can use the search bar and the links for the product will be shown to them. 

- **Seller Dashboard**
  The users has a dashboard page that shows the number of customers and orders of their products, monthly sales, customer demographics, order status update page, and listings.

- **Checkout and Payment** 
  The user will enter their location credentials with the help of Nominatim API that can recommend them verified addresses. For orders that are from or to the United States of America, the EasyPost API will provide rates and is converted into PHP (Philippine Peso). For orders that are from or to any point in the Philippines, a flat rate of Php 100 is set.

- **Messaging System**
  The user will receive a message once their account has been made. The users can send messages to sellers through the dashboard page.


## 📸 Before/After Performance Screenshots
| Before | After | 
|---------------------|--------------------|
| <img src="https://github.com/user-attachments/assets/abe0e3de-d40c-448f-8e38-e9d2b5e65eb9" width="500"/> |<img width="300" src="https://github.com/user-attachments/assets/b0e03979-4af7-4cf5-a61d-05849e436b27"/> |
|<img width="240" src="https://github.com/user-attachments/assets/41bf28fe-7953-43fb-ac4a-7195c9234877" /> |<img src="https://github.com/user-attachments/assets/edbaeb8e-1dc7-4d48-b16d-4be3a2aaa2e1" width="220"/> | 
| <img height="300" src="https://github.com/user-attachments/assets/46f4e80f-4e74-40bd-8270-50fff2866b90" />| <img width="300" src="https://github.com/user-attachments/assets/a6542454-c9cd-4e5a-92bb-f0f01ccc4ae7" />|
|<img height="240" src="https://github.com/user-attachments/assets/13b80533-c937-4f66-ab28-896e7e8322e5" /> |<img width="300" src="https://github.com/user-attachments/assets/49179aa1-12f3-4a48-ba49-7fc8d4862983" />|
Recent Changes November 24, 2025:
| <img width="2559" height="1305" alt="image" src="https://github.com/user-attachments/assets/b0c0cd13-e86b-46fd-9caf-84087270ddb4" /> | <img width="2339" height="1298" alt="image" src="https://github.com/user-attachments/assets/32e83349-660f-4aba-bace-793036778367" />|


## 🐞 Known Issues & Limitations
- **No payment gateway integration**  
  Orders are confirmed but not processed through real transactions.
- **Basic error handling**  
  Some forms lack detailed validation feedback, which may confuse users.
- **No image compression**  
  Uploaded product images are stored as-is, potentially affecting performance.
- **Manual deployment triggers**  
  Some deployment platforms may require manual redeploys if auto-deploy is misconfigured.
- **API rate limits not handled**  
  External APIs like Twilio and Quotable.io may fail silently if rate limits are exceeded.
- **Minimal accessibility features**  
  The site lacks ARIA labels and keyboard navigation enhancements for screen readers.
- **Mobile responsiveness may vary**  
  While designed to be responsive, some layouts may break on smaller screens.
- **EasyPost API**
  Given the limitations for the testing version, the API will only work if either the buyer or seller is from the United States of America. A flat rate of Php 100 is set for locations based in the Philippines.

## Admin test credentials
The Username and Password are in the submission bin comment box.

