# Start with a base image containing Java runtime
FROM openjdk:10-jdk-slim

# Add a volume pointing to /tmp
VOLUME /tmp

# Make port 8080 available to the world outside this container
EXPOSE 8080

ENV DEVELOPER_KEY=undefined
ENV CX=undefined

# The application's jar file
ARG JAR_FILE=target/anki-vocabulary-assistant-0.0.1.jar

# Add the application's jar to the container
ADD ${JAR_FILE} anki-vocabulary-assistant.jar
RUN mkdir /save
ADD mywiktionary.json /mywiktionary.json

# Build a shell script because the ENTRYPOINT command doesn't like using ENV
RUN echo "#!/bin/bash \n java -Djava.security.egd=file:/dev/./urandom -DdeveloperKey="${DEVELOPER_KEY}" -Dcx="${CX}" -DoutputDir="/save/" -DdictionaryFile="/mywiktionary.json" --add-modules java.xml.bind -jar /anki-vocabulary-assistant.jar" > ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Run the generated shell script.
ENTRYPOINT ["./entrypoint.sh"]

