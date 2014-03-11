INSERT INTO permission (id, name, visibility) VALUES (1, 'membership', 10);
INSERT INTO permission (id, name, visibility) VALUES (2, 'canCheckAccounts', 1000);
INSERT INTO permission (id, name, visibility) VALUES (3, 'canAssignAccounts', 10000);

INSERT INTO csa (kitty_id, name, annual_kitty_amount, default_account_threshold) VALUES
    ( (SELECT id FROM account WHERE gc_name='CASSA COMUNE'), 'Rete GAS Lucca', '1.0', '-100.0');
