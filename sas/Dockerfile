FROM openjdk:11-jdk

WORKDIR /sas

#COPY --chown=${USER} sas /home/${USER}/sas

COPY start.sh /sas/start.sh
RUN chmod +x /sas/start.sh

EXPOSE 8888

CMD ["/sas/start.sh"]
