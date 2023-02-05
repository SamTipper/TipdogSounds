FROM python:3.10.9-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN pip install py-cord==2.0.0b1

CMD ["sudo", "apt", "install", "ffmpeg"]

COPY . .

CMD [ "python3", "main.py" ]
