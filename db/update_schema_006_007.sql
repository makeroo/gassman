SET SESSION storage_engine = "MyISAM";

alter table account drop column gc_desc;
alter table account drop column gc_id;
alter table account drop column gc_parent;
alter table transaction drop column gc_id;
alter table transaction_line drop column gc_id;
