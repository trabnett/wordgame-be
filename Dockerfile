FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["./entrypoint.sh"]

EXPOSE 8181

CMD ["python", "manage.py", "runserver", "0.0.0.0:8181"]
