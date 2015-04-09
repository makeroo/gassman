
insert into delivery_place (description) values ('Asilo nido Il seme, Sant''Anna');
insert into delivery_place (description) values ('Tempagnano');
insert into delivery_place (description) values ('Pieve San Paolo');


-- creo il produttore irene e luciana (1)
insert into producer (name, description) values ('Luciana & Irene', 'Erbi, uova, polli, conigli etc.');
-- aggiungo simone pieraz come referente (può gestirne gli ordini)
insert into producer_person (producer_id, person_id, perm_id, csa_id) values (1, 1, 12, 1);

