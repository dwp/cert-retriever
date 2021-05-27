FROM python:3.8-alpine3.10

WORKDIR /app

# Data volume
VOLUME [ "/certificates" ]

RUN apk --update --no-cache add gcc musl-dev libffi-dev openssl-dev
RUN chown -R nobody:nogroup /certificates
RUN chown -R nobody:nogroup /app

COPY requirements.txt ./
RUN  pip install -r requirements.txt

COPY src/*.py ./

ENTRYPOINT ["python", "retrieve_all_certs.py"]
