FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN chmod +x /app/build.sh
RUN bash /app/build.sh

EXPOSE $PORT

CMD ["gunicorn", "the_pulse.wsgi:application", "--bind", "0.0.0.0:$PORT"]
