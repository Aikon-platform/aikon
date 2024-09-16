FROM openjdk:11-jdk

WORKDIR /cantaloupe

ENV USER=root

COPY --chown=${USER} cantaloupe /
RUN chmod +x /cantaloupe/start.sh

EXPOSE 8182

CMD ["/cantaloupe/start.sh"]
