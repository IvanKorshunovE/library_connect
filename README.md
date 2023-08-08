# LibraryConnect: Your Gateway to Seamless Library Operations and Bookings

The Library Service API is a comprehensive RESTful API designed for a library booking platform. It offers a wide range of endpoints, including user registration, authentication, profile management, borrowing creation and retrieval, stripe payments functionality, book and borrowing management (exclusive to administrators), and additional features.

## Requirements
- Python 3.x
- Django
- Django REST framework

### How to Run

1. Clone the repository: `git clone https://github.com/IvanKorshunovE/library_connect`
2. Change to the project directory (if you are not in the rood directory): `cd library_service_project`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate`
5. Install the required packages: `pip install -r requirements.txt`
6. Create a `.env` file by copying the `.env.sample` file and populate it with the required values.
7. Run migrations: `python manage.py migrate`
8. Create a test superuser, optionally create test books and borrowings
9. Install and adjust redis to your local machine or do the next step
10. If you can't install redis locally, run the Redis server from docker: `docker run -d -p 6379:6379 redis`
11. Run the Celery worker for task handling: `celery -A library_service_project worker -l INFO`
12. Run Celery beat for task scheduling: `celery -A library_service_project beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler`
13. Create a schedule for running sync in the DB (additionally, the periodic task with crontab schedule (At 04:00 AM Europe/Kyiv) is already created).
14. Run the app: `python manage.py runserver`

### API Documentation

The API is well-documented with detailed explanations of each endpoint and their functionalities. The documentation provides sample requests and responses to help you understand how to interact with the API. You can access the API documentation by visiting the following URL in your browser:
- [API Documentation](http://localhost:8000/api/schema/swagger-ui/)
