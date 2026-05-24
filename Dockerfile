FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN chmod +x /app/build.sh
RUN bash /app/build.sh

RUN chmod +x /app/entrypoint.sh

EXPOSE $PORT

ENTRYPOINT ["/app/entrypoint.sh"]
