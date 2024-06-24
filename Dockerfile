FROM python:3.12-alpine3.20

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ARG BASE_URL=/
EXPOSE 8000
CMD uvicorn main:app --host 0.0.0.0 --root-path ${BASE_URL}
