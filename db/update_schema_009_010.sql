SET SESSION storage_engine = "MyISAM";

ALTER TABLE account ADD COLUMN membership_fee DECIMAL(15,2) NOT NULL DEFAULT 0;
ALTER TABLE csa CHANGE annual_kitty_amount membership_fee  DECIMAL(15,2) NOT NULL DEFAULT 0;

INSERT INTO permission (id, name, visibility) VALUES (12, 'canEditAnnualKittyAmount', 1000);
