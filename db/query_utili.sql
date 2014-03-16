-- prospetto degli utenti e dei loro conti
select p.id, p.first_name, p.last_name, c.address, a.gc_name
 from person p
 join person_contact pc on pc.person_id=p.id
 join contact_address c on pc.address_id=c.id
 left join account a on a.id=p.current_account_id
 where c.kind='E'
 order by p.id;

-- conti e loro amount
select p.id, p.first_name, p.middle_name, p.last_name, a.id, sum(l.amount)
 from person p
 join account a on a.id=p.current_account_id
 join transaction_line l on l.account_id=a.id
 join transaction t on t.id=l.transaction_id
 where t.modified_by_id is null
 group by p.id, a.id;




-- persone senza conto
select p.id, p.first_name, p.last_name, c.address
 from person p
 join person_contact pc on pc.person_id=p.id
 join contact_address c on pc.address_id=c.id
 where c.kind='E' and p.current_account_id is null
 order by p.id;

-- conti non ancora assegnati
select * from account
 where id not in (select current_account_id from person where current_account_id is not null)
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
update person set current_account_id =83 where id=15;

