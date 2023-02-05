FROM ubuntu

WORKDIR ./

COPY . .

CMD [ "python3", "main.py" ]