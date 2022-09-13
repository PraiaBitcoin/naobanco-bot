FROM python:3.7

RUN apt-get update -y
RUN apt-get install git locales -y
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install -y python3-opencv
RUN apt-get install -y locales && \
    sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LANG pt_BR.UTF-8 
ENV LC_ALL pt_BR.UTF-8

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt --no-cache-dir

EXPOSE 80

CMD ["python3", "__main__.py"]
