SET SESSION storage_engine = "MyISAM";

ALTER TABLE account ADD COLUMN membership_fee DECIMAL(15,2) NOT NULL DEFAULT 0;
ALTER TABLE csa DROP COLUMN annual_kitty_amount;

INSERT INTO permission (id, name, visibility) VALUES (12, 'canEditMembershipFee', 1000);
