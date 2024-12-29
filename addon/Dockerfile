# Run main.py when the container launches
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM $BUILD_FROM

# Install dependencies
RUN apk add --no-cache python3 py3-pip 
RUN apk add --no-cache libusb

RUN rm /usr/lib/python*/EXTERNALLY-MANAGED && \
    python3 -m ensurepip && \
    pip3 install openant paho-mqtt


#RUN pipx install openant
#RUN pip install paho-mqtt

# Copy add-on files
COPY src ./src
#RUN chmod a+x /run.sh

# Set the start command
CMD ["python", "./src/main.py"]
