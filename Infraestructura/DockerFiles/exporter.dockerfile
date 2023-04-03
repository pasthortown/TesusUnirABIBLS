FROM python:3.8

WORKDIR /usr/src/app

COPY ExporterWS/requirements.txt ./
RUN apt-get update
RUN apt-get install -y wkhtmltopdf
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone

COPY ExporterWS/exporter.py .
COPY Templates ./Templates

EXPOSE 5050

CMD [ "python", "exporter.py" ]