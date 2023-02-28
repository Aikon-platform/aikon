It is possible to connect the Postgres database to a GUI, e.g. PGadmin.
Once PGadmin is installed

# Configure database server
https://stackoverflow.com/questions/61576670/databases-in-psql-dont-show-up-in-pgadmin4
localhost for Obs

# See data
Database > <dbname> > Schema > Public > Tables
select * from public.vhsapp_manuscript;
