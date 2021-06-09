FROM python:3.7
LABEL maintainer="pedro.cerqueira@medicina.ulisboa.pt"

WORKDIR /app
ADD . /app

EXPOSE 5000
ENV FLASK_APP ref_ns_security_run.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_DEBUG=1
ENV MAIL_USERNAME {{cookiecutter.flask_email}}
ENV MAIL_PASSWORD {{cookiecutter.flask_email_password}}

#RUN apk add --no-cache gcc musl-dev linux-headers
RUN pip install --upgrade pip
RUN pip install gunicorn

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# install BLAST+
RUN mkdir /blast
RUN cd ../blast; wget ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.10.0/ncbi-blast-2.10.0+-x64-linux.tar.gz \
&& tar -xzvf ncbi-blast-2.10.0+-x64-linux.tar.gz && rm ncbi-blast-2.10.0+-x64-linux.tar.gz
ENV PATH="/blast/ncbi-blast-2.10.0+/bin:${PATH}"

#ENTRYPOINT ["python","ref_ns_security_run.py"]
#CMD [ "flask", "run" ]

# Run container with gunicorn 
# More info about workers, threads and --worker-tmp-dir
# https://pythonspeed.com/articles/gunicorn-in-docker/
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "-w", "{{cookiecutter.gunicorn_workers}}", "--threads={{cookiecutter.gunicorn_threads}}", "--worker-class=gthread", "-b", "0.0.0.0:5000", "wsgi:app"]
