alter table delivery_place add column csa_id int not null ;

update state set name='Italia' where id=110;

insert into street_address (first_line, city_id) values ('Sant''Anna', 3680);
insert into street_address (first_line, city_id) values ('via di Tempagnano', 3680);
insert into street_address (first_line, city_id) values ('via dell''Osso', 3680);

insert into delivery_place (address_id, description, csa_id) values (1, 'Asilo nido Il seme, Sant''Anna', 1);
insert into delivery_place (address_id, description, csa_id) values (2, 'Tempagnano', 1);
insert into delivery_place (address_id, description, csa_id) values (3, 'Pieve San Paolo', 1);


-- creo il produttore irene e luciana (1)
insert into producer (name, description) values ('Luciana & Irene', 'Erbi, uova, polli, conigli etc.');
-- aggiungo simone pieraz come referente (può gestirne gli ordini)
insert into producer_person (producer_id, person_id, perm_id, csa_id) values (1, 1, 12, 1);

