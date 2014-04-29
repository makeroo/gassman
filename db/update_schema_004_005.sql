ALTER TABLE transaction ADD COLUMN csa_id INT REFERENCES csa(id);

UPDATE transaction SET csa_id = 1;

UPDATE transaction SET cc_type ='g' WHERE cc_type ='G';
UPDATE transaction SET cc_type ='d' WHERE cc_type ='D';
