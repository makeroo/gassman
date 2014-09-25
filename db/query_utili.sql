-- permessi escluso membership
select g.id, g.perm_id, x.name, p.id, p.first_name, p.last_name from permission_grant g join person p on p.id=g.person_id join permission x on g.perm_id=x.id where g.perm_id != 1 order by person_id, perm_id;


-- creare un profilo
insert into person (first_name, last_name) values ('Xxx', 'Xxx');
select * from person order by id desc limit 1;
insert into permission_grant (csa_id, person_id, perm_id) values (1, Xxx, 1);
insert into account (state, gc_id, gc_name, gc_type, gc_parent, csa_id, currency_id) values ('O', 'x279', '', 'ASSET', 'acf998ffe1edbcd44bc30850813650ac', 1, 1);
select * from account order by id desc limit 1;
insert into account_person (from_date, person_id, account_id) values (now(), PERSONID, ACCOUNTID);

-- prospetto degli utenti e dei loro conti
select p.id, p.first_name, p.last_name, c.address, a.gc_name, k.name
 from person p
 left join person_contact pc on pc.person_id=p.id
 left join contact_address c on pc.address_id=c.id
 left join account_person ap on ap.person_id=p.id
 left join account a on a.id=ap.account_id
 left join csa k on k.id=a.csa_id
 where ap.to_date is null and (c.kind='E' or c.kind is null)
 order by p.id;

-- persone senza permessi ma con conti (fantasmi)
select * from person where id not in (select person_id from permission_grant) and id in (select person_id from account_person);

-- persone senza permessi e senza conti (intrusi)
select * from person where id not in (select person_id from permission_grant) and id not in (select person_id from account_person);

-- trasformare i fantasmi in membri del gas
insert into permission_grant (csa_id, person_id, perm_id) select 1, id, 1 from person where id not in (select person_id from permission_grant) and id in (select person_id from account_person);

-- conti senza transazioni
select * from account where id not in
  (select distinct l.account_id from transaction_line l
                                join transaction t on t.id=l.transaction_id
                                where t.modified_by_id is null);

-- intervallo di attività di un conto...
select min(log.log_date), max(log.log_date)
  from transaction_line l
  join transaction t on l.transaction_id=t.id
  join transaction_log log on log.transaction_id=t.id
  where  l.account_id=58;

-- da controntarsi con from_date/to_date degli account_person...
select * from account_person where account_id =58;

-- gli account con problemi, ovvero il cui ap from è successivo a una qualsiasi transazione:
-- non tiene conto delle cointestazioni, eg angelo albero che si unisce a rosanna marinelli...
select distinct ap.id, AP.from_date, ap.person_id from transaction t join transaction_line l on l.transaction_id=t.id join transaction_log log on log.transaction_id=t.id join account_person ap on ap.account_id=l.account_id where ap.from_date > log.log_date order by ap.id;

-- conti non associati né a persone né a csa
--
select * from account where id not in (select account_id from account_person) and id not in (select account_id  from account_csa);

-- expenses
select * from account where gc_type ='EXPENSE';

-- persone che non hanno ancora acceduto
select *
 from person p
 where p.id not in (select pc.person_id from contact_address c join person_contact pc on c.id=pc.address_id where c.kind='I')
 ;


-- conti e loro amount
select p.id, p.first_name, p.middle_name, p.last_name, a.id, sum(l.amount), k.name
 from person p
 join account_person ap on ap.person_id=p.id
 join account a on a.id=ap.account_id
 join transaction_line l on l.account_id=a.id
 join transaction t on t.id=l.transaction_id
 join csa k on k.id=a.csa_id
 where t.modified_by_id is null and ap.to_date is null
 group by p.id, a.id;

-- conti anche senza persone e loro amount
select a.gc_name, sum(l.amount)
 from account a
 join transaction_line l on l.account_id=a.id
 join transaction t on t.id=l.transaction_id
 where t.modified_by_id is null
 group by a.id;

-- verifica partita doppia
-- QUESTA DEVE RISULTARE 0.00!
SELECT SUM(l.amount) FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id WHERE t.modified_by_id IS NULL ;

-- totale in cassa (contanti in mano al tesoriere)
SELECT SUM(l.amount) FROM transaction t JOIN transaction_line l ON l.transaction_id=t.id JOIN account a ON l.account_id=a.id WHERE t.modified_by_id IS NULL AND a.gc_type='ASSET';

-- persone senza conto
select p.id, p.first_name, p.last_name, c.address
 from person p
 join person_contact pc on pc.person_id=p.id
 join contact_address c on pc.address_id=c.id
 left join account_person ap on ap.person_id=p.id
 where c.kind='E' and ap.from_date is null
 order by p.id;

-- conti non ancora assegnati
-- non tiene conto dei conti non più intestati (to_date settato)
select * from account
 where id not in (select account_id from account_person where to_date is null)
;


-- profili doppi
-- uso: si trovano due profili (person) che riferiscono la stessa persona fisica
--      (ovviamente in maniera non automatica, tipo persone che si regisrano più
--      volte con account openid diversi)
-- si trovano i person_contact interessati
select p.id as pid, p.first_name, p.last_name,
       c.id as cid, c.address, c.kind, c.contact_type,
       pc.id as xid
  from person_contact pc
  join person p on pc.person_id=p.id
  join contact_address c on c.id=pc.address_id
  where p.id in (40,36);
-- quindi si assegnano i person_contact del person che si vuol buttare
-- al person che si vuol tenere
update person_contact set person_id=36 where id in (79,80);
-- NB: una cosa del genere, cioè un passo solo, non si può fare:
-- update person_contact set person_id=36 where id in (select pc.id from person_contact pc join person p on pc.person_id=p.id join contact_address c on c.id=pc.address_id where p.id =40);
-- ERROR 1093 (HY000): You can't specify target table 'person_contact' for update in FROM clause

-- verificare se un profilo (person) ha dati associati
select * from person_contact where person_id=40;
select * from account_person where person_id=40;
select * from permission_grant where person_id=40;


select * from account where gc_name like '%igong%';
insert into account_person (from_date, person_id, account_id) values (now(), 83, 15);

