FROM python:3.8.6-slim

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

RUN ["pytest"]

ENTRYPOINT ["python"]
CMD ["-u", "-m", "Server"]