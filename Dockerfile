FROM python:3.11.9-alpine3.20

WORKDIR /app
COPY * /app/

RUN pip3 install -r requirements.txt

CMD ["/app/sms_bridge.py"]
