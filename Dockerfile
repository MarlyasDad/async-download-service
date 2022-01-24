FROM python:3.9-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends zip unzip gcc libpython3.9-dev

COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN pip install -r ./requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "./server.py"]