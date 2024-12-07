FROM python:3.12-bookworm AS dependencies

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


FROM dependencies

COPY . .
EXPOSE 8000
CMD [ "fastapi", "run" ]
