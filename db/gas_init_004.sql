ALTER TABLE transaction ADD COLUMN cc_type CHAR(1) NOT NULL DEFAULT 'G';

INSERT INTO account_person (from_date, person_id, account_id)
  SELECT now(), id, current_account_id FROM person WHERE current_account_id IS NOT NULL;

ALTER TABLE person DROP COLUMN current_account_id;
