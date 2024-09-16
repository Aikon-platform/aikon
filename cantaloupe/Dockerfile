FROM openjdk:11-jdk

WORKDIR /cantaloupe

COPY --chown=root cantaloupe/* /canteloupe/
RUN chmod +x /cantaloupe/start.sh

EXPOSE 8182

CMD ["/cantaloupe/start.sh"]
