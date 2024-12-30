# Run main.py when the container launches
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM $BUILD_FROM


# Install dependencies
RUN apk add --no-cache python3 py3-pip 
RUN apk add --no-cache libusb
RUN apk add --no-cache git

RUN git clone https://github.com/Tigge/openant.git
WORKDIR /openant
RUN git reset --hard b3492bbc3b9dd88570942f43a8c35b276b6fa8cf
RUN pip3 install .

RUN python3 -m ensurepip && \
    pip3 install paho-mqtt

#RUN python3 -m ensurepip && \
#    pip3 install openant

#RUN pipx install openant
#RUN pip install paho-mqtt
WORKDIR /
# Copy add-on files
COPY src ./src
COPY run.sh ./run.sh
RUN chmod a+x /run.sh

# Set the start command
CMD ["python3", "src/main.py"]
