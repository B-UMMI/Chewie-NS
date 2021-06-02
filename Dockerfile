FROM python:3.7
LABEL maintainer="pedro.cerqueira@medicina.ulisboa.pt"

WORKDIR /app
ADD . /app

EXPOSE 5000
ENV FLASK_APP ref_ns_security_run.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_DEBUG=1
ENV MAIL_USERNAME testing_ns@ns.com
ENV MAIL_PASSWORD testing_ns

#RUN apk add --no-cache gcc musl-dev linux-headers
RUN pip install --upgrade pip
RUN pip install gunicorn

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# install BLAST+
RUN mkdir /blast
RUN cp -r ncbi-blast-2.10.1+ ../blast
# RUN cd ../blast; wget ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.10.0/ncbi-blast-2.10.0+-x64-linux.tar.gz \
# && tar -xzvf ncbi-blast-2.10.0+-x64-linux.tar.gz && rm ncbi-blast-2.10.0+-x64-linux.tar.gz
ENV PATH="/blast/ncbi-blast-2.10.1+/bin:${PATH}"

#ENTRYPOINT ["python","ref_ns_security_run.py"]
#CMD [ "flask", "run" ]

# Run container with gunicorn 
# More info about workers, threads and --worker-tmp-dir
# https://pythonspeed.com/articles/gunicorn-in-docker/
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "-w", "4", "--threads=2", "--worker-class=gthread", "-b", "0.0.0.0:5000", "wsgi:app"]
