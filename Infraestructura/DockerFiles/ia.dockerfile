FROM python:3.8

WORKDIR /usr/src/app

COPY IAWS/requirements.txt ./
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone
RUN python -m spacy download es_core_news_sm
COPY IAWS/ia.py .

EXPOSE 5050

CMD [ "python", "ia.py" ]