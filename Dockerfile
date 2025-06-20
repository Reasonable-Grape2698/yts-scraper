FROM python:3.14-rc-slim
WORKDIR /app
COPY . .
RUN pip3 install setuptools
RUN python3 setup.py install
