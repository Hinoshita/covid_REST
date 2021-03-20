FROM python:3
WORKDIR /myapp
COPY . /myapp
RUN pip install -r requirements.txt
EXPOSE 80
CMD ["python", "run.py"]