FROM openjdk:11-jdk
#FROM maven:3.8-openjdk-11

WORKDIR /sas

ENV USER=aikon

RUN apt-get update && apt-get install -y maven

#COPY proxy.xml /root/.m2/settings.xml
RUN mkdir -p /root/.m2 && \
    echo '<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0" \
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
       xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd"> \
       <proxies> \
           <proxy> \
               <id>proxy</id> \
               <active>true</active> \
               <protocol>http</protocol> \
               <host>proxy.enpc.fr</host> \
               <port>3128</port> \
           </proxy> \
       </proxies> \
    </settings>' > /root/.m2/settings.xml

COPY --chown=${USER} sas /sas

RUN chmod +x /sas/start.sh

EXPOSE 8888

CMD ["/sas/start.sh"]
