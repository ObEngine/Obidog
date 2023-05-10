FROM alpine:3.17

RUN apk add python3 py3-pip doxygen clang-extra-tools git

WORKDIR /app

COPY README.md setup.py ./

RUN pip install -e .

COPY Doxyfile .
COPY hints ./hints
COPY obidog ./obidog
COPY static ./static
COPY templates ./templates

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]