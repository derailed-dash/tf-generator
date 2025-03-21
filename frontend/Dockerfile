FROM python:3.12

EXPOSE 8080
WORKDIR /app

COPY . /app/frontend/

RUN pip install -r /app/frontend/requirements.txt
ENV PYTHONPATH=/app

ENTRYPOINT ["streamlit", "run", "frontend/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
