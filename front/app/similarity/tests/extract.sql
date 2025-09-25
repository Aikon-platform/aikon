-- USAGE
-- psql -U <user_name> -d <database> -p <port> -f ./path/to/extract.sql

-- retrieve the files from the docker using:
-- sudo docker cp docker-db-1:/data_digitization.csv .;
-- sudo docker cp docker-db-1:/data_regionpair.csv .;
-- sudo docker cp docker-db-1:/data_regions.csv .;
-- sudo docker cp docker-db-1:/data_witness.csv .;
-- sudo docker cp docker-db-1:/data_edition.csv .;
-- sudo docker cp docker-db-1:/data_place.csv .;

-- instead of using WITH..AS CTEs, we create views:
-- it is not possibly to use psql \copy with CTEs,
-- and CTEs are only available within the current statement,
-- so it's not possible to access the CTEs after ";"

-- delete possibly existing views
DROP VIEW IF EXISTS pl;
DROP VIEW IF EXISTS ed_pid;
DROP VIEW IF EXISTS ed;
DROP VIEW IF EXISTS wt_eid;
DROP VIEW IF EXISTS wt;
DROP VIEW IF EXISTS dg_wid;
DROP VIEW IF EXISTS dg;
DROP VIEW IF EXISTS rg_did;
DROP VIEW IF EXISTS rg;
DROP VIEW IF EXISTS rp_rid;
DROP VIEW IF EXISTS rp;

-- first 100 regionpairs
CREATE TEMPORARY VIEW rp AS
    SELECT *
    FROM webapp_regionpair
    ORDER BY webapp_regionpair.id ASC
    LIMIT 100;
-- regions ids of the regionpairs
CREATE TEMPORARY VIEW rp_rid AS
    SELECT rp.regions_id_1 AS rid
    FROM  rp
    UNION (
        SELECT rp.regions_id_2 AS rid
        FROM rp
    );
-- regions associated to the first 100 regionpairs
CREATE TEMPORARY VIEW rg AS
    SELECT *
    FROM webapp_regions
    WHERE webapp_regions.id IN (
        SELECT rp_rid.rid FROM rp_rid
    );
-- digitization ids from rg
CREATE TEMPORARY VIEW rg_did AS
    SELECT DISTINCT rg.digitization_id AS did
    FROM rg;
-- digitizations
CREATE TEMPORARY VIEW dg AS
    SELECT *
    FROM webapp_digitization
    WHERE webapp_digitization.id IN (
        SELECT rg_did.did FROM rg_did
    );
-- witness ids in dg
CREATE TEMPORARY VIEW dg_wid AS
    SELECT DISTINCT dg.witness_id AS wid
    FROM dg;
-- all witnesses
CREATE TEMPORARY VIEW wt AS
    SELECT *
    FROM webapp_witness
    WHERE webapp_witness.id IN (
        SELECT dg_wid.wid FROM dg_wid
    );
CREATE TEMPORARY VIEW wt_eid AS
    SELECT DISTINCT wt.edition_id as eid
    FROM wt;
CREATE TEMPORARY VIEW ed AS
    SELECT *
    FROM webapp_edition
    WHERE webapp_edition.id IN (
        SELECT wt_eid.eid FROM wt_eid
    );
CREATE TEMPORARY VIEW ed_pid AS
    SELECT DISTINCT ed.place_id AS pid
    FROM ed;
CREATE TEMPORARY VIEW pl AS
    SELECT *
    FROM webapp_place
    WHERE webapp_place.id IN (
        SELECT ed_pid.pid FROM ed_pid
    );

-- run exports
\copy ( SELECT * FROM rp ) TO './webapp_regionpair.csv' WITH (FORMAT CSV, HEADER);
\copy ( SELECT * FROM rg ) TO './webapp_regions.csv' WITH (FORMAT CSV, HEADER);
\copy ( SELECT * FROM dg ) TO './webapp_digitization.csv' WITH (FORMAT CSV, HEADER);
\copy ( SELECT * FROM wt ) TO './webapp_witness.csv' WITH (FORMAT CSV, HEADER);
\copy ( SELECT * FROM ed ) TO './webapp_edition.csv' WITH (FORMAT CSV, HEADER);
\copy ( SELECT * FROM pl ) TO './webapp_place.csv' WITH (FORMAT CSV, HEADER);
