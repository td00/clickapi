FROM python:3.9-slim
WORKDIR /app
COPY app.py /app/
RUN pip install flask
RUN touch counter.db
EXPOSE 3000
CMD ["python", "app.py"]
