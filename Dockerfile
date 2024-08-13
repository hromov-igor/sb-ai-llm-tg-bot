FROM python:3.12

WORKDIR /code

COPY requirements.txt /code
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /code
CMD ["python", "./main.py"]
