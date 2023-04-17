FROM python:3.8

WORKDIR /usr/src/app

COPY BackendMainWS/requirements.txt ./
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone
COPY BackendMainWS/backend_main.py .

EXPOSE 5050

CMD [ "python", "backend_main.py" ]