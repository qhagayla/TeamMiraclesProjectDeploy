# DESIGN OF A WEB-BASED DOCUMENT MANAGEMENT SYSTEM FOR ON-THE-JOB TRAINEES

Current features
----------------

# Pre-requisites:
- [Any Python-3 version](https://www.python.org/downloads/)
- [PostgreSQL database](https://www.postgresql.org/download/)

# Installation

## Seach Terminal in the Window
```
git clone https://github.com/qhagayla/TeamMiraclesProject.git
```
```
cd django-lms
```
```
python -m venv venv
```
```
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
```
./venv/Scripts/activate
```
```
dir
```
```
pip install -r requirements.txt
```
## Install postgre --> https://www.postgresql.org/download/windows/
## Search in the Window "pgAdmin 4" and then create database

## Click on the server properties and go to connection

## Create .env file on the django-lms and type this and change the bracket
```
DB_NAME=dms_for_ojt_trainees
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=
USER_EMAIL=qhagayla@tip.edu.ph
USER_PASSWORD=1234
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
```
```
python manage.py makemigrations
```
```
python manage.py migrate
```
```
python manage.py createsuperuser
```
```
python manage.py runserver
```



