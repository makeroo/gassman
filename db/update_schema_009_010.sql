SET SESSION storage_engine = "MyISAM";

ALTER TABLE account ADD COLUMN annual_kitty_amount DECIMAL(15,2) NOT NULL DEFAULT 0;

INSERT INTO permission (id, name, visibility) VALUES (12, 'canEditAnnualKittyAmount', 1000);
