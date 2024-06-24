FROM python:3.12-alpine3.20

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000
CMD uvicorn main:app
