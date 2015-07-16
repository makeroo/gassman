alter table delivery_place add column csa_id int not null ;

insert into delivery_place (description, csa_id) values ('Asilo nido Il seme, Sant''Anna', 1);
insert into delivery_place (description, csa_id) values ('Tempagnano', 1);
insert into delivery_place (description, csa_id) values ('Pieve San Paolo', 1);


-- creo il produttore irene e luciana (1)
insert into producer (name, description) values ('Luciana & Irene', 'Erbi, uova, polli, conigli etc.');
-- aggiungo simone pieraz come referente (può gestirne gli ordini)
insert into producer_person (producer_id, person_id, perm_id, csa_id) values (1, 1, 12, 1);

