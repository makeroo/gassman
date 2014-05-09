CREATE TABLE account_csa (
  id INT NOT NULL AUTO_INCREMENT,
  csa_id INT NOT NULL,
  account_id INT NOT NULL,

  FOREIGN KEY (csa_id) REFERENCES csa(id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  PRIMARY KEY (id)
);

insert into account_csa (csa_id, account_id) select id, kitty_id from csa;

ALTER TABLE csa DROP COLUMN kitty_id;
ALTER TABLE csa DROP COLUMN expenses_id;
ALTER TABLE csa DROP COLUMN income_id;
