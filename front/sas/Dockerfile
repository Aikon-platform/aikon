FROM eclipse-temurin:11
#FROM eclipse-temurin:11-jdk
#FROM openjdk:11-jdk
#FROM maven:3.8-openjdk-11

WORKDIR /sas

ENV USER=aikon
ENV SAS_PORT=${SAS_PORT:-8888}

RUN apt-get update && apt-get install -y maven

EXPOSE ${SAS_PORT:-8888}

COPY --chown=${USER} sas /sas
RUN chmod +x /sas/start.sh
CMD ["/sas/start.sh"]

# maybe no need to run last three commands if this is added to docker-compose
# working_dir: /sas
# command: mvn jetty:run -Djetty.port=${SAS_PORT:-8888}
# sas content would be directly mounted using volumes directive
