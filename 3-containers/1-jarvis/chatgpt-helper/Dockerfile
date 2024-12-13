FROM python:slim-bullseye

USER root

# Install dependencies
RUN apt update -y

# Create new user
RUN adduser --disabled-password autouser

# Copy over scripts
COPY server.py /home/autouser/scripts/server.py
COPY read_configmap.py /home/autouser/scripts/read_configmap.py
COPY helper.py /home/autouser/scripts/helper.py

# Set permissions
RUN chown autouser:autouser -R /home/autouser/scripts
RUN chmod +x /home/autouser/scripts/*.py

# Install python modules
RUN pip3 install requests \
    && pip3 install boto3 \
    && pip3 install openai

# Change user
USER autouser

# Change directory
WORKDIR /home/autouser/scripts

# Run script on start
CMD [ "python3", "server.py" ]
