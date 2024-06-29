FROM python:3.10.14-slim as dev

COPY requirements.txt .
RUN apt-get update && apt-get -y install zsh git
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "/bin/zsh" ]