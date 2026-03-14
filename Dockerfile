FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["./entrypoint.sh"]

EXPOSE 8181

CMD ["daphne", "-b", "0.0.0.0", "-p", "8181", "config.asgi:application"]
