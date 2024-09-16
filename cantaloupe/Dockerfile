FROM openjdk:11-jdk

WORKDIR /cantaloupe

#COPY --chown=${USER} cantaloupe /home/${USER}/cantaloupe

COPY cantaloupe/start.sh /cantaloupe/start.sh
RUN chmod +x /cantaloupe/start.sh

EXPOSE 8182

CMD ["/cantaloupe/start.sh"]
