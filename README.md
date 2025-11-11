# HandaCraftPH-Overview
HandaCraftPH is designed as a culturally conscious marketplace system that supports MSMEs and traditional artisans through customizable workflows and role-based access.

## Tech stack & version numbers.

| Component   | Platform | Justification |
|-------------|----------| --------------- |
| Front-End   | HTML (structure), CSS (visuals), and JS (interactivity)   | Fast load times, responsive design, and broad browser compatibility |
| Back-End    | Django   | Secure, scalable, and comes with built-in tools for rapid development |
| Database    | SQLite   | Lightweight, fast, and ideal for small to medium-sized projects |
| External APIs / services | Twilio, Easypost API, Quotable.io | 

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
## Deployment link.
The live site is hosted on Render:  (https://handacraftph.onrender.com)
## Before/after performance screenshots.

## 🐞 Known Issues & Limitations
- **No payment gateway integration**  
  Orders are confirmed but not processed through real transactions.
- **Limited scalability with SQLite**  
  SQLite may not handle high traffic or concurrent writes efficiently.
- **Basic error handling**  
  Some forms lack detailed validation feedback, which may confuse users.
- **No image compression**  
  Uploaded product images are stored as-is, potentially affecting performance.
- **No admin dashboard**  
  Seller management is done via basic views without a centralized admin interface.
- **Manual deployment triggers**  
  Some deployment platforms may require manual redeploys if auto-deploy is misconfigured.
- **API rate limits not handled**  
  External APIs like Twilio and Quotable.io may fail silently if rate limits are exceeded.
- **Minimal accessibility features**  
  The site lacks ARIA labels and keyboard navigation enhancements for screen readers.
- **Mobile responsiveness may vary**  
  While designed to be responsive, some layouts may break on smaller screens.
