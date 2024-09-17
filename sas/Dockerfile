#FROM openjdk:11-jdk
#
#WORKDIR /sas
#
#ENV USER=aikon
#
#RUN apt-get update && apt-get install -y maven
#
#COPY --chown=${USER} sas/* /sas
#RUN chmod +x /sas/start.sh
#
#EXPOSE 8888
#
#CMD ["/sas/start.sh"]

#FROM maven:3-jdk-11
#WORKDIR /sas
#ENV USER=aikon
#COPY --chown=${USER} sas/* /sas
#RUN chmod +x /sas/start.sh
#CMD ["/sas/start.sh"]

FROM maven:3-jdk-11 AS buildstage
WORKDIR /usr/src/sas
COPY --chown=${USER} sas/* /usr/src/sas
ARG MVN_ARGS="-DskipTests"
RUN mvn $MVN_ARGS package

FROM tomcat:9-jre11 AS runstage
#RUN rm -r /usr/local/tomcat/webapps/*
RUN mkdir /annotation-data
COPY --from=buildstage /usr/src/sas/target/simpleAnnotationStore /usr/local/tomcat/webapps/ROOT
COPY sas/docker/sas-tomcat/sas.properties /usr/local/tomcat/webapps/ROOT/WEB-INF

EXPOSE 8888
CMD ["catalina.sh", "run"]
