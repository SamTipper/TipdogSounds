FROM python:3.11.2-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN pip install py-cord

RUN apt-get update -y

RUN apt-get install ffmpeg -y

COPY . .

CMD [ "python3", "main.py" ]
