FROM python:3.13-slim

WORKDIR /app

RUN apt-get update
RUN pip install --upgrade pip poetry

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main && \
    poetry cache clear pypi --all && \
    rm -rf /root/.cache

COPY . .

CMD python run.py
