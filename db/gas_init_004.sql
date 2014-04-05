ALTER TABLE transaction ADD COLUMN cc_type CHAR(1) NOT NULL DEFAULT 'G';

INSERT INTO account_person (from_date, person_id, account_id)
  SELECT now(), id, current_account_id FROM person WHERE current_account_id IS NOT NULL;

ALTER TABLE person DROP COLUMN current_account_id;

ALTER TABLE permission_grant MODIFY perm_id INT;
ALTER TABLE permission_grant ADD FOREIGN KEY (perm_id) REFERENCES permission(id);
ALTER TABLE permission_grant ADD FOREIGN KEY (person_id) REFERENCES person(id);
ALTER TABLE permission_grant ADD FOREIGN KEY (csa_id) REFERENCES csa(id);


CREATE TABLE transaction_log (
  id INT NOT NULL AUTO_INCREMENT,

--  cassa_id int not null,
  log_date DATETIME NOT NULL,
  operator_id INT NOT NULL,

  op_type CHAR(1) NOT NULL, -- (A)dded, (D)eleted, (M)odified, (e)rror
  transaction_id INT NOT NULL,
  notes TEXT, -- in caso di errore, il motivo

  FOREIGN KEY (operator_id) REFERENCES person(id),
  FOREIGN KEY (transaction_id) REFERENCES transaction(id),
  PRIMARY KEY (id)
);

ALTER TABLE csa ADD COLUMN expenses_id INT NOT NULL;
ALTER TABLE csa ADD COLUMN income_id INT NOT NULL;

ALTER TABLE csa ADD FOREIGN KEY (kitty_id) REFERENCES account(id);
ALTER TABLE csa ADD FOREIGN KEY (expenses_id) REFERENCES account(id);
ALTER TABLE csa ADD FOREIGN KEY (income_id) REFERENCES account(id);

update csa set income_id=(select id from account where gc_type='INCOME');
update csa set expenses_id = ( select id from account where gc_type='EXPENSE' AND gc_parent=(select gc_id from account where gc_type='ROOT'));
