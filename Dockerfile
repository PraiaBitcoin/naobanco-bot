FROM python:3.7

RUN apt-get update -y
RUN apt-get install git -y

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt --no-cache-dir

EXPOSE 9651

CMD ["python3", "__main__.py"]
