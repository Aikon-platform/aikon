FROM openjdk:11-jdk
#FROM maven:3.8-openjdk-11

WORKDIR /sas

ENV USER=aikon
ENV SAS_PORT=${SAS_PORT:-8888}

RUN echo 'Acquire::http::Proxy "http://195.221.193.15:3128";' > /etc/apt/apt.conf.d/proxy.conf && \
    echo 'Acquire::https::Proxy "http://195.221.193.15:3128";' >> /etc/apt/apt.conf.d/proxy.conf && \
    echo 'Acquire::CompressionTypes::Order:: "gz";' > /etc/apt/apt.conf.d/99disable-compressors && \
    echo 'APT::Get::AllowUnauthenticated "true";' >> /etc/apt/apt.conf.d/99disable-compressors
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
               <host>195.221.193.15</host> \
               <port>3128</port> \
           </proxy> \
       </proxies> \
    </settings>' > /root/.m2/settings.xml

EXPOSE ${SAS_PORT:-8888}

COPY --chown=${USER} sas /sas
RUN chmod +x /sas/start.sh
CMD ["/sas/start.sh"]

# maybe no need to run last three commands if this is added to docker-compose
# working_dir: /sas
# command: mvn jetty:run -Djetty.port=${SAS_PORT:-8888}
# sas content would be directly mounted using volumes directive
