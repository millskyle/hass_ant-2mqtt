# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
#WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY src ./src

# Install any needed packages specified in requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y libusb-1.0-0-dev \
    && rm -rf /var/lib/apt/lists/*

# Install openant
RUN pip install openant paho-mqtt pyusb libusb pyyaml

# Make port 80 available to the world outside this container
#EXPOSE 80

# Run main.py when the container launches
CMD ["python", "./src/main.py"]
