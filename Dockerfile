FROM python:3.13-slim
WORKDIR /study
COPY code/requirements.txt /study/code/requirements.txt
RUN pip install --no-cache-dir -r code/requirements.txt
COPY . /study
RUN pip install --no-cache-dir setuptools && pip install --no-deps --no-build-isolation .
CMD ["python", "code/check_availability.py"]
