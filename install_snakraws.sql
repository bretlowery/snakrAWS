DROP TABLE IF EXISTS snakraws_factevents;
DROP TABLE IF EXISTS snakraws_dimcities;
DROP TABLE IF EXISTS snakraws_dimcontinents;
DROP TABLE IF EXISTS snakraws_dimcountries;
DROP TABLE IF EXISTS snakraws_dimdevices;
DROP TABLE IF EXISTS snakraws_dimuseragents;
DROP TABLE IF EXISTS snakraws_dimhosts;
DROP TABLE IF EXISTS snakraws_dimips;
DROP TABLE IF EXISTS snakraws_dimregions;
DROP TABLE IF EXISTS snakraws_dimpostalcodes;
DROP TABLE IF EXISTS snakraws_dimshorturls;
DROP TABLE IF EXISTS snakraws_dimlongurls;
DROP TABLE IF EXISTS snakraws_dimreferers;

create table snakraws_dimcities (
  id             BIGINT       NOT NULL PRIMARY KEY,
  name           VARCHAR(100) NOT NULL UNIQUE,
  is_blacklisted BOOLEAN      NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimcities (id, name, is_blacklisted)
VALUES (5298596870147225945, 'unknown', Null);
INSERT INTO snakraws_dimcities (id, name, is_blacklisted)
VALUES (-8478403668358870585, 'missing', Null);
INSERT INTO snakraws_dimcities (id, name, is_blacklisted)
VALUES (-3750763034362895579, '', Null);

create table snakraws_dimregions (
  id             BIGINT       NOT NULL PRIMARY KEY,
  name           VARCHAR(100) NOT NULL UNIQUE,
  code           CHAR(2)      NOT NULL UNIQUE,
  is_blacklisted BOOLEAN      NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimregions (id, name, is_blacklisted, code)
VALUES (5298596870147225945, 'unknown', Null, '??');
INSERT INTO snakraws_dimregions (id, name, is_blacklisted, code)
VALUES (-8478403668358870585, 'missing', Null, '!!');
INSERT INTO snakraws_dimregions (id, name, is_blacklisted, code)
VALUES (-3750763034362895579, '', Null, '--');

create table snakraws_dimpostalcodes (
  id             BIGINT       NOT NULL PRIMARY KEY,
  postalcode     VARCHAR(32)  NOT NULL UNIQUE,
  is_blacklisted BOOLEAN      NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimpostalcodes (id, postalcode, is_blacklisted)
VALUES (5298596870147225945, 'unknown', Null);
INSERT INTO snakraws_dimpostalcodes (id, postalcode, is_blacklisted)
VALUES (-8478403668358870585, 'missing', Null);
INSERT INTO snakraws_dimpostalcodes (id, postalcode, is_blacklisted)
VALUES (-3750763034362895579, '', Null);

create table snakraws_dimcountries (
  id             BIGINT       NOT NULL PRIMARY KEY,
  name           VARCHAR(100) NOT NULL UNIQUE,
  code           CHAR(2)      NOT NULL UNIQUE,
  is_blacklisted BOOLEAN      NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimcountries (id, name, is_blacklisted, code)
VALUES (5298596870147225945, 'unknown', Null, '??');
INSERT INTO snakraws_dimcountries (id, name, is_blacklisted, code)
VALUES (-8478403668358870585, 'missing', Null, '!!');
INSERT INTO snakraws_dimcountries (id, name, is_blacklisted, code)
VALUES (-3750763034362895579, '', Null, '--');

create table snakraws_dimcontinents (
  id             BIGINT       NOT NULL PRIMARY KEY,
  name           VARCHAR(100) NOT NULL UNIQUE,
  code           CHAR(2)      NOT NULL UNIQUE,
  is_blacklisted BOOLEAN      NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimcontinents (id, name, is_blacklisted, code)
VALUES (5298596870147225945, 'unknown', Null, '??');
INSERT INTO snakraws_dimcontinents (id, name, is_blacklisted, code)
VALUES (-8478403668358870585, 'missing', Null, '!!');
INSERT INTO snakraws_dimcontinents (id, name, is_blacklisted, code)
VALUES (-3750763034362895579, '', Null, '--');

create table snakraws_dimdevices (
  id             BIGINT       NOT NULL PRIMARY KEY,
  deviceid       VARCHAR(40)  NOT NULL UNIQUE,
  is_blacklisted BOOLEAN      NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimdevices (id, deviceid, is_blacklisted)
VALUES (5298596870147225945, 'unknown', Null);
INSERT INTO snakraws_dimdevices (id, deviceid, is_blacklisted)
VALUES (-8478403668358870585, 'missing', Null);
INSERT INTO snakraws_dimdevices (id, deviceid, is_blacklisted)
VALUES (-3750763034362895579, '', Null);

create table snakraws_dimuseragents (
  id             BIGINT        NOT NULL PRIMARY KEY,
  useragent      VARCHAR(8192) NOT NULL UNIQUE,
  is_blacklisted BOOLEAN       NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimuseragents (id, useragent, is_blacklisted)
VALUES (5298596870147225945, 'unknown', Null);
INSERT INTO snakraws_dimuseragents (id, useragent, is_blacklisted)
VALUES (-8478403668358870585, 'missing', Null);
INSERT INTO snakraws_dimuseragents (id, useragent, is_blacklisted)
VALUES (-3750763034362895579, '', Null);

create table snakraws_dimhosts (
  id             BIGINT       NOT NULL PRIMARY KEY,
  host           VARCHAR(253) NOT NULL UNIQUE,
  is_blacklisted BOOLEAN      NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimhosts (id, host, is_blacklisted)
VALUES (5298596870147225945, 'unknown', Null);
INSERT INTO snakraws_dimhosts (id, host, is_blacklisted)
VALUES (-8478403668358870585, 'missing', Null);
INSERT INTO snakraws_dimhosts (id, host, is_blacklisted)
VALUES (-3750763034362895579, '', Null);

create table snakraws_dimips (
  id             BIGINT       NOT NULL PRIMARY KEY,
  ip             VARCHAR(39)  NOT NULL UNIQUE,
  is_blacklisted BOOLEAN      NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimips (id, ip, is_blacklisted)
VALUES (5298596870147225945, 'unknown',  Null);
INSERT INTO snakraws_dimips (id, ip, is_blacklisted)
VALUES (-8478403668358870585, 'missing',  Null);
INSERT INTO snakraws_dimips (id, ip, is_blacklisted)
VALUES (-3750763034362895579, '', Null);

create table snakraws_dimlongurls (
    id BIGINT PRIMARY KEY,
    longurl VARCHAR(4096) NOT NULL,
    originally_encoded BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO snakraws_dimlongurls (id, longurl, is_active)
VALUES (4967328134902799212, 'unspecified', TRUE);

create table snakraws_dimshorturls (
    id BIGINT PRIMARY KEY,
    longurl_id BIGINT NOT NULL,
    shorturl VARCHAR(40) NOT NULL,
    shorturl_path_size SMALLINT NULL,
    compression_ratio DECIMAL(10,2) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO snakraws_dimshorturls (id, longurl_id, shorturl, shorturl_path_size, is_active)
VALUES (4967328134902799212, 4967328134902799212, 'unspecified', null, TRUE);

ALTER TABLE snakraws_dimshorturls
ADD CONSTRAINT fk_snakraws_shorturls_longurl_id
FOREIGN KEY (longurl_id) REFERENCES snakraws_dimlongurls (id) ON DELETE NO ACTION;

create table snakraws_dimreferers (
  id             BIGINT        NOT NULL PRIMARY KEY,
  referer        VARCHAR(1024) NOT NULL UNIQUE,
  is_blacklisted BOOLEAN       NULL DEFAULT FALSE
);

INSERT INTO snakraws_dimreferers (id, referer, is_blacklisted)
VALUES (5298596870147225945, 'unknown',  Null);
INSERT INTO snakraws_dimreferers (id, referer, is_blacklisted)
VALUES (-8478403668358870585, 'missing',  Null);
INSERT INTO snakraws_dimreferers (id, referer, is_blacklisted)
VALUES (-3750763034362895579, '', Null);

create table snakraws_factevents (
  id               SERIAL PRIMARY KEY,
  event_yyyymmdd   CHAR(8) DEFAULT TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDD') NOT NULL,
  event_hhmiss     CHAR(6) DEFAULT TO_CHAR(CURRENT_TIMESTAMP, 'HH24MISS') NOT NULL,
  event_type       CHAR(1) NOT NULL CHECK (event_type IN ('B','D','E','I','L','R','S','W','X')),
  http_status_code SMALLINT                                           NOT NULL,
  info             VARCHAR(8192)                                      NOT NULL,
  longurl_id       BIGINT                                             NOT NULL,
  shorturl_id      BIGINT                                             NOT NULL,
  city_id          BIGINT                                             NOT NULL,
  region_id        BIGINT                                             NOT NULL,
  postalcode_id    BIGINT                                             NOT NULL,
  country_id       BIGINT                                             NOT NULL,
  continent_id     BIGINT                                             NOT NULL,
  device_id        BIGINT                                             NOT NULL,
  host_id          BIGINT                                             NOT NULL,
  referer_id       BIGINT                                             NOT NULL,
  ip_id            BIGINT                                             NOT NULL,
  useragent_id     BIGINT                                             NOT NULL,
  blacklisted_csv  VARCHAR(256)                                       NOT NULL DEFAULT ''
);

CREATE INDEX IX_snakraws_factevents_shorturl  ON snakraws_factevents
  (shorturl_id);

CREATE INDEX IX_snakraws_factevents_longurl  ON snakraws_factevents
  (longurl_id);

CREATE INDEX IX_snakraws_factevents_yyyymmdd_hhmiss ON snakraws_factevents
  (event_yyyymmdd, event_hhmiss);

CREATE INDEX IX_snakraws_factevents_type_yyyymmdd_hhmiss ON snakraws_factevents
  (event_type, event_yyyymmdd, event_hhmiss);

CREATE INDEX IX_snakraws_factevents_city
ON snakraws_factevents
  (city_id);

CREATE INDEX IX_snakraws_factevents_continent
ON snakraws_factevents
  (continent_id);

CREATE INDEX IX_snakraws_factevents_country
ON snakraws_factevents
  (country_id);

CREATE INDEX IX_snakraws_factevents_device
ON snakraws_factevents
  (device_id);

CREATE INDEX IX_snakraws_factevents_host
ON snakraws_factevents
  (host_id);

CREATE INDEX IX_snakraws_factevents_ip
ON snakraws_factevents
  (ip_id);

CREATE INDEX IX_snakraws_factevents_postalcode
ON snakraws_factevents
  (postalcode_id);

CREATE INDEX IX_snakraws_factevents_referer
ON snakraws_factevents
  (referer_id);

CREATE INDEX IX_snakraws_factevents_region
ON snakraws_factevents
  (region_id);

CREATE INDEX IX_snakraws_factevents_useragent
ON snakraws_factevents
  (useragent_id);

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_longurl_id
FOREIGN KEY (longurl_id)
REFERENCES snakraws_dimlongurls (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_shorturl_id
FOREIGN KEY (shorturl_id)
REFERENCES snakraws_dimshorturls (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_city_id
FOREIGN KEY (city_id)
REFERENCES snakraws_dimcities (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_country_id
FOREIGN KEY (country_id)
REFERENCES snakraws_dimcountries (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_continent_id
FOREIGN KEY (continent_id)
REFERENCES snakraws_dimcontinents (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_region_id
FOREIGN KEY (region_id)
REFERENCES snakraws_dimregions (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_postalcode_id
FOREIGN KEY (postalcode_id)
REFERENCES snakraws_dimpostalcodes (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_device_id
FOREIGN KEY (device_id)
REFERENCES snakraws_dimdevices (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_host_id
FOREIGN KEY (host_id)
REFERENCES snakraws_dimhosts (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_referer_id
FOREIGN KEY (referer_id)
REFERENCES snakraws_dimreferers (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_ip_id
FOREIGN KEY (ip_id)
REFERENCES snakraws_dimips (id) ON DELETE NO ACTION;

ALTER TABLE snakraws_factevents ADD CONSTRAINT fk_snakraws_factevents_useragent_id
FOREIGN KEY (useragent_id)
REFERENCES snakraws_dimuseragents (id) ON DELETE NO ACTION;


