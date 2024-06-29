FROM python:3.10.14-slim as dev

COPY ./solution/requirements.txt .
RUN apt-get update && apt-get -y install zsh git default-jre default-jdk
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "/bin/zsh" ]