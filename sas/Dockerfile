FROM openjdk:11-jdk

WORKDIR /sas

COPY start.sh /sas/start.sh
RUN chmod +x /sas/start.sh

EXPOSE 8888

CMD ["/sas/start.sh"]
