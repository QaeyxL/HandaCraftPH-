# HandaCraftPH-Overview
HandaCraftPH is designed as a culturally conscious marketplace system that supports MSMEs and traditional artisans through customizable workflows and role-based access.

## Tech stack & version numbers.

| Component   | Platform | Justification | Version |
|-------------|-------------| --------------- | ----- |
| Front-End   | HTML (structure), CSS (visuals), and JS (interactivity)   | Fast load times, responsive design, and broad browser compatibility | |
| Back-End | Django | Secure, scalable, and comes with built-in tools for rapid development |5.2.8|
| Database | SQLite | Lightweight, fast, and ideal for small to medium-sized projects | 3.50.4| 
| External APIs / services | 1. Twilio</br> 2. Easypost API </br> 3. Quotable.io | | 1. 9.8.5 |

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
## 📸 Before/After Performance Screenshots
| Before | After | 
|---------------------|--------------------|
| <img src="https://github.com/user-attachments/assets/abe0e3de-d40c-448f-8e38-e9d2b5e65eb9" width="500"/> |<img width="300" src="https://github.com/user-attachments/assets/b0e03979-4af7-4cf5-a61d-05849e436b27"/> |
|<img width="240" src="https://github.com/user-attachments/assets/41bf28fe-7953-43fb-ac4a-7195c9234877" /> |<img src="https://github.com/user-attachments/assets/edbaeb8e-1dc7-4d48-b16d-4be3a2aaa2e1" width="220"/> | 
| <img height="300" src="https://github.com/user-attachments/assets/46f4e80f-4e74-40bd-8270-50fff2866b90" />| <img width="300" src="https://github.com/user-attachments/assets/a6542454-c9cd-4e5a-92bb-f0f01ccc4ae7" />|
|<img height="240" src="https://github.com/user-attachments/assets/13b80533-c937-4f66-ab28-896e7e8322e5" /> |<img width="300" src="https://github.com/user-attachments/assets/49179aa1-12f3-4a48-ba49-7fc8d4862983" />|

## 🐞 Known Issues & Limitations
- **No payment gateway integration**  
  Orders are confirmed but not processed through real transactions.
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
