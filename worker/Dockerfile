FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/fizfox

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY worker/README.md ./worker/README.md

RUN useradd --create-home --uid 10001 fizfox
USER 10001

EXPOSE 8080

CMD ["python", "-c", "print('FizFox worker image ready; execution is delegated to the isolated worker boundary')"]
