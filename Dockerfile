FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN python -m unittest discover -s tests -t .
CMD ["python", "-m", "chaos_monkey", "compare", "--seed", "1", "--out", "out"]
