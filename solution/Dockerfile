FROM python:3.12.4-slim as dev

COPY ./solution/requirements.txt .
RUN apt-get update && apt-get -y install zsh git 
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "/bin/zsh" ]