ALTER TABLE csa CHANGE default_account_treshold default_account_threshold DECIMAL(15,2) NOT NULL DEFAULT 0;
ALTER TABLE csa ADD COLUMN name VARCHAR(255);
ALTER TABLE csa ADD COLUMN description TEXT;
ALTER TABLE permission ADD COLUMN ord INT NOT NULL DEFAULT 0;
