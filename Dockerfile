FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Set the working directory in the container
WORKDIR /content

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y \
        libgl1 \
        libglib2.0-0 \
        python3-pip \
        python-is-python3 \
        python3.10-dev \
        bash \
        gcc \
        build-essential \
#        wget \
#        git \
#        git-lfs \
#        curl \
        libffi-dev \
        libssl-dev \
        openssl \
#        tcl-dev \
#        tk-dev \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /content/requirements.txt
RUN pip3 install -r /content/requirements.txt

COPY . /content

CMD ["python", "app.py"]