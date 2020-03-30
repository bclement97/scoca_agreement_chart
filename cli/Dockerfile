FROM python:2.7

COPY requirements.txt /cli/requirements.txt
RUN pip install -r /cli/requirements.txt

COPY . /cli/

ENTRYPOINT ["python"]
CMD ["-m", "cli"]
