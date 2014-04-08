ALTER TABLE inscriptions_equipier ADD COLUMN "verifier" bool NOT NULL DEFAULT false;
ALTER TABLE inscriptions_equipier ADD COLUMN "licence_manquante" bool NOT NULL DEFAULT false;
ALTER TABLE inscriptions_equipier ADD COLUMN "certificat_manquant" bool NOT NULL DEFAULT false;
ALTER TABLE inscriptions_equipier ADD COLUMN "autorisation_manquante" bool NOT NULL DEFAULT false;
ALTER TABLE inscriptions_equipier ADD COLUMN "valide" bool NOT NULL DEFAULT false;
ALTER TABLE inscriptions_equipier ADD COLUMN "erreur" bool NOT NULL DEFAULT false;
ALTER TABLE inscriptions_equipier ADD COLUMN "homme" bool NOT NULL DEFAULT false;

