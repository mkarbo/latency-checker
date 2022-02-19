FROM python:3.9.10
RUN apt update -y 
RUN apt-get install build-essential gcc -y
RUN pip install --upgrade pip setuptools wheel
RUN pip install poetry

COPY python-ping/pyproject.toml /app/pyproject.toml
COPY python-ping/python_ping /app/python_ping

WORKDIR /app

RUN poetry config virtualenvs.create true
RUN cd /app/ && poetry install --no-interaction

CMD [ "poetry run python", "python_ping/main.py" ]
