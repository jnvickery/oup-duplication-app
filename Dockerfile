FROM python:3.9-slim

EXPOSE 8501

WORKDIR /app

COPY . /app

RUN python -m pip install -r requirements.txt

# ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
CMD ["streamlit", "run", "app.py"]
