FROM openjdk:11-jdk

WORKDIR /sas

ENV USER=aikon

RUN apt-get update && apt-get install -y maven

COPY --chown=${USER} sas /

#COPY sas/start.sh /sas/start.sh
RUN chmod +x /sas/start.sh

EXPOSE 8888

CMD ["/sas/start.sh"]
