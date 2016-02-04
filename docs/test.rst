- utente che non appartiene a csa
  accesso
  richiesta

  select * from person where id not in (select person_id from account_person) limit 1;

- utente che appartiene a csa e basta

  conto aperto:
  select * from person p join account_person ap on ap.person_id=p.id where ap.to_date is null and p.id not in (select person_id from permission_grant) limit 1;

  con conto singolo intestato
  con conto cointestato

  select ap.account_id, count(ap.person_id)
    from account_person ap
   where ap.person_id in (select p.id
                            from person p
                            join account_person ap on ap.person_id=p.id
                           where ap.to_date is null and
                                 p.id not in (select person_id from permission_grant) )
                        group by ap.account_id;

  accesso transazione a caso
  accesso conto a caso

  conto chiuso:
  select * from person p join account_person ap on ap.person_id=p.id where ap.to_date is not null and p.id not in (select person_id from permission_grant) limit 1;

- can check accounts
  navigazione membri
  modifica filtro e ritorna

- can view contacts
  navigazione membri
  modifica filtro e ritorna

- can check accounts + can view contacts
  navigazione membri
  modifica filtro e ritorna

- registra scambio
  modifica
  cancella

- registra pagamenti 1 (no compensazione)
  modifica
  cancella

- registra pagamenti 2 (solo compensazione)
  modifica
  cancella

- membership fee
  modifica
  cancella

- profilo persona
  modifica & salva

- chiusura conto
