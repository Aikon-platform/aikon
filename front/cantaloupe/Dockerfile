FROM eclipse-temurin:11

WORKDIR /cantaloupe

COPY --chown=root cantaloupe/* /cantaloupe/
RUN chmod +x /cantaloupe/start.sh

EXPOSE ${CANTALOUPE_PORT:-8182}

CMD ["/cantaloupe/start.sh"]
