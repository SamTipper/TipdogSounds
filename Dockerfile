FROM ubuntu

WORKDIR ./

COPY requirements requirements

COPY . .

CMD [ "python3", "main.py" ]