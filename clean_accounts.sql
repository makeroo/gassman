
UPDATE person SET current_account_id=NULL;
DELETE FROM account_person;
UPDATE csa SET kitty_id=NULL;
DELETE FROM transaction_line;
DELETE FROM transaction;
