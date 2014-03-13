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

   
select * from account where gc_name like '%igong%';
update person set current_account_id =83 where id=15;

