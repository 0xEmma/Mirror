FROM python:latest
COPY . .
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn
CMD gunicorn --workers=3 --bind 0.0.0.0:8000 app:app