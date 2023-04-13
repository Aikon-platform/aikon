It is possible to connect the Postgres database to a GUI, e.g. PGadmin.
Once PGadmin is installed

# Configure database server
https://stackoverflow.com/questions/61576670/databases-in-psql-dont-show-up-in-pgadmin4
localhost for Obs

# See data
Database > <dbname> > Schema > Public > Tables > Right-click on desired table > View

```sql
select * from public.<table-name>;
```

# Evolution of data model on production

1. Export production database in SQL
   1. Connect to production server
   2. `pg_dump -h localhost -U <db-user> -d <db-name> > $(date +%Y-%m-%d)_dump.sql`
2. Copy migrations files and database dump from production server to local
   1. Disconnect from production server
   2. `scp <user>@<host-server>:~/<YYYY-MM-DD>_dump.sql ~`
3. Locally, create a new database and fill it with production data
   1. ```bash
      sudo -u postgres psql
      postgres=# CREATE DATABASE <new-db-name>;
      postgres=# GRANT ALL PRIVILEGES ON DATABASE <new-db-name> TO <db-user>;
      postgres=# \q
      ```
   2. `psql -h localhost -d <new-db-name> -U <db-user> -f ~/<YYYY-MM-DD>_dump.sql`
4. Apply migrations files on that new database to reproduce the data model on production
5. Import production SQL script into local database
6. Look at the data if everything is correct
7. Execute makemigrations command
8. See what happen
9. Check data on PGadmin + on the interface
10. If everything is alright, export local database as SQL script
11. Create a new branch with migrationfiles + modified model files and push them on production server
12. Create or use a second database on production
13. Import the first SQL script (unmodified database)
14. Change the database name in .env to correspond to this new db
15. Apply migrate command on production
16. Check if everything is alright
