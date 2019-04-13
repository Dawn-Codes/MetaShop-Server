FROM ubuntu:18.04
RUN apt-get update && apt-get install -y python-opencv
RUN apt-get install libxrender1
COPY . /app
RUN make /app
CMD python /app/app.py