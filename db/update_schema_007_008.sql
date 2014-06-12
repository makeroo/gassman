SET SESSION storage_engine = "MyISAM";

ALTER TABLE person ADD COLUMN account_notifications CHAR(1) NOT NULL DEFAULT 'E';

CREATE TABLE producer (
  id INT NOT NULL AUTO_INCREMENT,

  name VARCHAR(100),
  description TEXT,
  -- TODO: blog

  PRIMARY KEY (id)
);

CREATE TABLE producer_person (
  id INT NOT NULL AUTO_INCREMENT,
  producer_id INT NOT NULL,
  person_id INT NOT NULL,

  FOREIGN KEY (producer_id) REFERENCES producer(id) ON DELETE CASCADE,
  FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE,
  PRIMARY KEY (id)
);

