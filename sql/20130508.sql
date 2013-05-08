CREATE TABLE "inscriptions_ville" (
    "id"       integer NOT NULL PRIMARY KEY,
    "lat"      decimal NOT NULL,
    "lng"      decimal NOT NULL,
    "nom"      varchar(200) NOT NULL,
    "region"   varchar(200) NOT NULL,
    "pays"     varchar(200) NOT NULL,
    "response" varchar(65535) NOT NULL
);
ALTER TABLE "inscriptions_equipier" ADD COLUMN "ville2_id"        integer REFERENCES "inscriptions_ville" ("id");
ALTER TABLE "inscriptions_equipe"   ADD COLUMN "gerant_ville2_id" integer REFERENCES "inscriptions_ville" ("id");

