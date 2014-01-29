create table state (
  -- anagrafe degli stati, praticamente una tabella costante
  -- quindi chi la riferisce non gestisce on delete
  -- non storicizzata

  id int not null,
  iso3 char(3) not null,
  name varchar(100) not null,

  primary key (id),
  unique (iso3)
);

create table city (
  -- anagrafe dei comuni, praticamente costante come gli stati
  -- (perà dobbiamo prevedere di poter aggiungere quelle straniere)
  -- uso una tabella per poter gestire i form degli indirizzi in
  -- autocompletamento

  id int not null,
  name varchar(200) not null,
  zip_code varchar(10) not null,
  state_id int not null,

  primary key (id)
);

create table street_address (
  id int not null,
  first_line varchar(200),
  second_line varchar(200),
  city_id int,
  zip_code varchar(10),
  --state_id varchar(3), -- lo recupero dalla città
  description text,

  primary key (id)
);

alter table street_address
  add constraint street_address_state_id_fk
  foreign key (state_id)
  references state(iso3);

create table contact_address (
  id int not null,
  address varchar(100),
  kind char(1) not null, -- (T)elephone, (M)obile, (E)mail, (F)ax
  contact_type varchar(20), -- testo libero: cell, ufficio, casa...

  primary key (id)
);

create table delivery_place (
  -- punto di consegna
  id int not null,
  address_id int not null,
  description text,

  primary key (id)
);

create table person (
  id int not null,
  first_name varchar (100),
  middle_name varchar (100),
  last_name varchar (100),
  default_delivery_place_id int,
  address_id int,
  current_account_id int,

  primary key (id)
);

create table person_contact (
  id int not null,

  person_id not null,
  address_id not null,
  priority int not null default 0,

  primary key (id)
);

create table turn (
  id int not null,

  turn_date date not null,
  delivery_place_id int not null,
  person_id int not null,
  work_type char(100), -- testo libero: apertura, consegna...

  primary key (id)
);

create table producer (
  id int not null,

  persone
  nome
  descrizione
  prodotto
  conto

  primary key (id)
);

create table product (
  id int not null,

  descrizione
  a-unità: prezzo unitario
  a-peso: prezzo peso (eg. formaggio)

  primary key (id)
);


ordine-singolo-produttore
  produttore
  partecipanti
   persona


create table cassa (
  id int not null,
  description text,

  primary key (id)
);


create table account (
  id int not null,
  state char(1) not null, -- (O)pen, (C)losing, close(D), (F)usion pending

  cassa_id int not null,
--  saldo CURRENCY not null, -- magari si calcola con una join?
-- perché potrei avere problemi di concorrenza

  primary key (id)
);

create table account_person (
  -- una volta che una persona diventa intestataria di un conto si crea
  -- una riga qui, con from_date che è la data da cui inizia l'intestazione
  -- se la persona cambia conto, qui si registra in to_date la data in cui
  -- smette di essere intestataria
  -- quindi l'intestazione è valida, cioè si può addebitare sul conto,
  -- solo se to_date è null
  -- mantengo la storicizzazione per poter mostrare alle persone la loro
  -- storia di movimenti non solo limitatamente all'ultimo conto di cui
  -- sono intestatari

  id int not null,
  from_date date not null,
  to_date date,
  person_id int not null,
  account_id int not null,

  primary key (id)
);

create table account_request (
  -- quando una persona richiede la cointestazione di un conto
  -- creo una riga qui per ogni intestatario
  -- se tutti danno l'assenso (Y) o smettono di essere intestatari (U)
  -- allora dò accesso, cioè cancello tutte le account_request e creo
  -- una account_person

  id int not null,
  account_id int not null, -- recuperabile da account_owner_id ma meglio duplicarlo
  requester_id int not null,
  account_owner_id int not null,
  use_granted char(1) not null default 'X', -- (X)tobeanswered, (Y)es, (N)o, (U)nnecessary anymore (requester not owner anymore)

  primary key (id),
  unique (requester_id) -- una persona può richiedere accesso ad un conto alla volta
);


create table transaction (
  id int not null,

  cassa_id int not null,
  description varchar(200),
  transaction_date date not null,

  -- le transazioni possono essere modificate
  -- la modifica crea una nuova transazione e la vecchia rimane
  -- ma viene marcata come cancellata valorizzando modified_by_id
  -- con l'id della nuova
  modified_by_id int, -- fk alla transazione che sovrascrive (annullando) questa

  primary key (id)
);

create table transaction_line (
  id int not null,

  transaction_id int not null,
  account_id int not null,
  description varchar(200),
  amount number(6,2) not null,
  -- currency

  primary key (id)
);


create table cassa_log (
  id int not null,

  cassa_id int not null,
  log_date date not null,
  operator_id int not null,

  op_type char(1) not null, -- Added, Deleted, Modified
  transaction_id int not null,

  primary key (id)
);

create table  (
  id int not null,

  primary key (id)
);

todo:
cassa in inglese
alcune tabelle
gli ordini
agganciare le transazioni agli ordini
contestazione delle transazioni
l'autenticazione si fa con openid
ma ci deve essere lo stato dell'account:
 * raccomandato da
 * valori di limite (sulla cassa, tipo soglie pre acquisto)
