ALTER TABLE person ADD COLUMN rss_feed_id CHAR(64);

CREATE TABLE currency (
  id INT NOT NULL AUTO_INCREMENT,
  iso_4217 CHAR(3),
  symbol VARCHAR(4) NOT NULL,
  description TEXT,

  PRIMARY KEY (id)
);

INSERT INTO currency (id, iso_4217, symbol) VALUES (1, 'EUR', '€');

ALTER TABLE account ADD COLUMN csa_id INT REFERENCES csa(id);

UPDATE account SET csa_id=1;

ALTER TABLE account MODIFY csa_id INT NOT NULL;

ALTER TABLE account ADD COLUMN currency_id INT REFERENCES currency(id);

UPDATE account SET currency_id=1;

ALTER TABLE account MODIFY csa_id INT NOT NULL;
