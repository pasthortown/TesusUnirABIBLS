FROM python:3.8

WORKDIR /usr/src/app

COPY BackendWSBack/requirements.txt ./
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone
COPY BackendWSBack/backend_main_back.py .

EXPOSE 5050

CMD [ "python", "backend_main_back.py" ]