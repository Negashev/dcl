FROM alpine

# install python
RUN apk add --no-cache ca-certificates python3

RUN apk add --no-cache --virtual .build-deps py3-pip openssl build-base python3-dev \
    && pip3 install --no-cache-dir ruamel.yaml \
    && apk del .build-deps \
    && rm -rf /var/cache/apk/* /tmp/*

ENTRYPOINT ["local-develop"]

ADD local-develop.py /bin/local-develop

RUN chmod +x /bin/local-develop
