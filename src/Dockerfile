FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
RUN pip install pipenv
ADD Pipfile /code/
ADD Pipfile.lock /code/

RUN pipenv install --system
ADD . /code/

CMD gunicorn potato.wsgi
