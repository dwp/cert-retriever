FROM python:3.8-alpine3.10

WORKDIR /app

RUN apk --update --no-cache add python gcc musl-dev libffi-dev openssl-dev
RUN chown -R nobody:nogroup /certificates/

COPY requirements.txt ./
RUN  pip install -r requirements.txt

COPY src/*.py ./

# Data volume
VOLUME [ "/certificates" ]

ENTRYPOINT ["python", "retrieve_all_certs.py"]
