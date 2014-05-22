CREATE TABLE account_csa (
  id INT NOT NULL AUTO_INCREMENT,
  csa_id INT NOT NULL,
  account_id INT NOT NULL,

  FOREIGN KEY (csa_id) REFERENCES csa(id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  PRIMARY KEY (id)
);

insert into account_csa (csa_id, account_id) select id, kitty_id from csa;
insert into account_csa (csa_id, account_id) select id, expenses_id from csa;
insert into account_csa (csa_id, account_id) select id, income_id from csa;

ALTER TABLE csa DROP COLUMN kitty_id;
ALTER TABLE csa DROP COLUMN expenses_id;
ALTER TABLE csa DROP COLUMN income_id;

INSERT INTO permission (id, name, visibility) VALUES (7, 'canEnterCashExchange', 1000);
INSERT INTO permission (id, name, visibility) VALUES (8, 'canEnterWithdrawal', 2000);

-- tutti i conti ad adarita (account del marito)
insert into permission_grant(csa_id, person_id, perm_id) values (1,97,2);
-- ad elena
insert into permission_grant(csa_id, person_id, perm_id) values (1,4,2);
-- mariarita non ha account: è un problema

-- tutti i permessi a me
insert into permission_grant(csa_id, person_id, perm_id) values (1,1,4);
insert into permission_grant(csa_id, person_id, perm_id) values (1,1,5);
insert into permission_grant(csa_id, person_id, perm_id) values (1,1,6);
insert into permission_grant(csa_id, person_id, perm_id) values (1,1,7);
insert into permission_grant(csa_id, person_id, perm_id) values (1,1,8);
