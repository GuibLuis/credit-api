
# Credit API

This API is part of a job application test. 

It has two different uses on the same (and only) route. It returns the three best credit offers from institutions if all parameter values are provided — or fewer, if no full matches are found.

CPFs available:
* 111.111.111-11 
* 123.123.123.12 
* 222.222.222.22

More about the routes and general information in: (will add the url here if/when i deploy it online, you can use the local one instead)

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`URL_START_POINT`


## Run Locally

Clone the project

```bash
  git clone https://github.com/GuibLuis/credit-api
```

Go to the project directory

```bash
  cd credit-api
```

Install dependencies

```bash
  pip install fastapi
  pip install uvicorn
  pip install python-dotenv
```

Start the API

```bash
  uvicorn main:app
```

See the document about the API after the start

```bash
  http://127.0.0.1:8000/docs#/
```
