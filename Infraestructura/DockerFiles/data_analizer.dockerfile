FROM python:3.8

WORKDIR /usr/src/app

COPY DataAnalizer/requirements.txt ./
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone
RUN python -m spacy download es_core_news_sm
COPY DataAnalizer/data_analizer.py .

CMD [ "python", "data_analizer.py" ]