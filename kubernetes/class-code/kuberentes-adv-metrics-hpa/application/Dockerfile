FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 5000

ENV BURN_MULTIPLIER=1000 \
    BURN_TICK=0.05 \
    BURN_MAX=100

CMD ["python", "app.py"]
