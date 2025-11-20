FROM eclipse-temurin:11-jdk
#FROM maven:3.8-openjdk-11

WORKDIR /sas

ENV USER=aikon
ENV SAS_PORT=${SAS_PORT:-8888}

RUN apt-get update && apt-get install -y maven

# for deployment on a server using proxy
#RUN mkdir -p /root/.m2 && \
#    echo '<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0" \
#       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
#       xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd"> \
#       <proxies> \
#           <proxy> \
#               <id>proxy</id> \
#               <active>true</active> \
#               <protocol>http</protocol> \
#               <host>proxy.enpc.fr</host> \
#               <port>3128</port> \
#           </proxy> \
#       </proxies> \
#    </settings>' > /root/.m2/settings.xml

EXPOSE ${SAS_PORT:-8888}

COPY --chown=${USER} sas /sas
RUN chmod +x /sas/start.sh
CMD ["/sas/start.sh"]

# maybe no need to run last three commands if this is added to docker-compose
# working_dir: /sas
# command: mvn jetty:run -Djetty.port=${SAS_PORT:-8888}
# sas content would be directly mounted using volumes directive
