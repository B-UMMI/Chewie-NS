FROM python:3.7
LABEL maintainer="pedro.cerqueira@medicina.ulisboa.pt"

WORKDIR /app
ADD . /app

EXPOSE 5000
ENV FLASK_APP ref_ns_security_run.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_DEBUG=1

#RUN apk add --no-cache gcc musl-dev linux-headers
RUN pip install --upgrade pip
RUN pip install gunicorn

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

#ENTRYPOINT ["python","ref_ns_security_run.py"]
#CMD [ "flask", "run" ]

# Run container with gunicorn 
# More info about workers, threads and --worker-tmp-dir
# https://pythonspeed.com/articles/gunicorn-in-docker/
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "-w", "7", "--threads=3", "--worker-class=gthread", "-b", "0.0.0.0:5000", "wsgi:app"]

