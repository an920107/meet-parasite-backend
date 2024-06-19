# Meet Parasite Backend

## Description

This project is to serve the backend of the meet parasite, so that the clients can change data with each others.

## Development

### Framework

- Using Python FastAPI.
- Connecting method:
  - Server -> Clients: web socket
  - Clients -> Server: http methods
    > Using http to send data to server because FastAPI has a convenient and perfect type checking, which helps avoid some basic problems.

### Usage

#### Run Python Server

1. (Optional) Create a Python virtual environment and use it.

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install the dependencies.

   ```bash
   pip install -r requirements.txt
   ```

3. Host the server with uvicorn.

   ```bash
   uvicorn main:app
   ```

   > The default port is 8000. There is a auto-generated document at <http://localhost:8000/redoc> and <http://localhost:8000/docs>

#### Run Client Website

> The client website is just an example to show that how to connect with the server, which is developed with Next.js.

1. Navigate to [`client_example`](./client_example/)

2. Install the dependencies.

   ```bash
   yarn install
   ```

   or using npm

   ```bash
   npm install
   ```

3. Start the website

   ```bash
   yarn run dev
   ```

   or using npm

   ```bash
   npm run dev
   ```

   > The default port is 3000. Browsing <http://localhost:3000> and try it!
