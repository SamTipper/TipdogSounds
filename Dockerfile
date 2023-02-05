FROM ubuntu

WORKDIR ./

COPY requirements requirements

RUN pip install -r ./requirements.txt

COPY . .

CMD [ "python3", "main.py" ]