FROM python:3

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN pip install py-cord==2.0.0b1

COPY . .

CMD [ "python3", "main.py" ]