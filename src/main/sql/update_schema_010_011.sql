SET SESSION storage_engine = "MyISAM";

alter table delivery_place add column csa_id int not null ;

insert into street_address (first_line, city_id) values ('Sant''Anna', 3680);
insert into street_address (first_line, city_id) values ('via di Tempagnano', 3680);
insert into street_address (first_line, city_id) values ('via dell''Osso', 3680);

insert into delivery_place (address_id, description, csa_id) values (1, 'Asilo nido Il seme, Sant''Anna', 1);
insert into delivery_place (address_id, description, csa_id) values (2, 'Tempagnano', 1);
insert into delivery_place (address_id, description, csa_id) values (3, 'Pieve San Paolo', 1);


update state set name='Italia' where id=110;


