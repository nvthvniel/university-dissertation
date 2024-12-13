FROM python:slim-bullseye

USER root

# Install dependencies
RUN apt update -y

# Create new user
RUN adduser --disabled-password autouser

# Copy over scripts
COPY server.py /home/autouser/scripts/server.py
COPY read_configmap.py /home/autouser/scripts/read_configmap.py
COPY put_item.py /home/autouser/scripts/put_item.py
COPY get_item.py /home/autouser/scripts/get_item.py
COPY delete_item.py /home/autouser/scripts/delete_item.py

# Set permissions
RUN chown autouser:autouser -R /home/autouser/scripts
RUN chmod +x /home/autouser/scripts/*.py

# Install python modules
RUN pip3 install boto3

# Change user
USER autouser

# Change directory
WORKDIR /home/autouser/scripts

# Run script on start
CMD [ "python3", "server.py" ]
