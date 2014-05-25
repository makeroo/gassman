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

-- conti senza transazioni
select * from account where id not in
  (select distinct l.account_id from transaction_line l
                                join transaction t on t.id=l.transaction_id
                                where t.modified_by_id is null);

-- expenses
select * from account where gc_type ='EXPENSE';

-- persone non ancora registrate
select * from account
 where gc_parent = 'acf998ffe1edbcd44bc30850813650ac'
   and gc_id not in ('4d5b627c2ec72d94d95e95543aa5cd1f', '5ba64cec222104efb491ceafd6dd1812')
   and id not in (select distinct account_id from account_person)
 order by gc_name;


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
 group by p.id, a.id;

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
select * from account
 where id not in (select account_id from account_person where to_date is null)
   and gc_parent = 'acf998ffe1edbcd44bc30850813650ac';

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

