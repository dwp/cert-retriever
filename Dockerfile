FROM python:3.8-alpine3.10

WORKDIR /app

# Data volume
VOLUME [ "/certificates" ]

COPY requirements.txt ./
COPY src/*.py ./

RUN apk --update --no-cache add gcc musl-dev libffi-dev openssl-dev
RUN pip install -r requirements.txt


ENTRYPOINT ["python", "retrieve_all_certs.py"]
