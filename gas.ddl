CREATE TABLE state (
  -- Anagrafe degli stati, praticamente una tabella costante.
  -- Non voglio gestire anche la storicizzazione, cioè aggiungere
  -- l'intervallo temporale all'interno del quale è valido un record.
  -- Questo perché la nostra anagrafica non ha pretese di ufficialità
  -- (questioni fiscali, etc.) quindi se gli stati nascono o spariscono
  -- è abbastanza irrilevante.

  id INT NOT NULL AUTO_INCREMENT,
  iso3 CHAR(3) NOT NULL,
  name VARCHAR(100) NOT NULL,

  PRIMARY KEY (id),
  UNIQUE (iso3)
);

CREATE TABLE city (
  -- Anagrafe dei comuni, praticamente costante come gli stati.
  -- La tabella ha lo scopo di gestire i form degli indirizzi in
  -- autocompletamento.
  -- Poiché gestiamo anche gli indirizzi stranieri, nuovi record
  -- possono essere aggiunti a runtime.

  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(200) NOT NULL,
  -- Lo zip code in italia è il cap. Le grandi città hanno più di un cap.
  -- In quei casi qui è indicato quello principale, negli indirizzi
  -- (vedi street_address) si riporta lo specifico.
  -- Eg. Pisa è 56100, San Piero, frazione di Pisa è 56125.
  -- Non mi interessa normalizzare gli zip code o validarli.
  zip_code VARCHAR(10),
  state_id INT NOT NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (state_id) REFERENCES state(id)
);

CREATE TABLE street_address (
  -- Gli indirizzi li gestisco in realzione molti a molti,
  -- anche se di fatto l'interfaccia web si limiterà a una
  -- associazione 1:1 (ogni persona avrà il suo indirizzo, anche
  -- chi convive...)

  id INT NOT NULL AUTO_INCREMENT,
  first_line VARCHAR(200), -- Eg. via Spippoli 45a
  second_line VARCHAR(200), -- Eg. Scala, c/o, Frazione, etc.
  city_id INT,
  zip_code VARCHAR(10), -- In italia le grandi città hanno più di un cap. Qui o si ripete quello della città o si indica lo specifico.
  --state_id int, -- Lo recupero dalla città.
  description TEXT, -- Note aggiuntive per raggiungere la persona, eg. "Suonare XXX".

  PRIMARY KEY (id),
  FOREIGN KEY (city_id) REFERENCES city(id)
);

CREATE TABLE contact_address (
  id INT NOT NULL AUTO_INCREMENT,
  address VARCHAR(100), -- Il numero del telefono, l'indirzzo email, etc.
  kind CHAR(1) NOT NULL DEFAULT 'M', -- (T)elephone, (M)obile, (E)mail, (F)ax
  contact_type VARCHAR(20), -- Testo libero: cell, ufficio, casa...

  PRIMARY KEY (id)
);

CREATE TABLE delivery_place (
  -- punto di consegna

  id INT NOT NULL AUTO_INCREMENT,
  address_id INT NOT NULL,
  description TEXT,

  PRIMARY KEY (id)
);

-- TODO: permessi

CREATE TABLE person (
  id INT NOT NULL AUTO_INCREMENT,

  first_name VARCHAR(100),
  middle_name VARCHAR(100),
  last_name VARCHAR(100),
  default_delivery_place_id INT,
  address_id INT,
  current_account_id INT,
  cash_treshold DECIMAL(15,2) NOT NULL DEFAULT 0,

  PRIMARY KEY (id),
  FOREIGN KEY (address_id) REFERENCES street_address(id),
  -- TODO: FOREIGN KEY (current_account_id) REFERENCES account(id)
);

CREATE TABLE person_contact (
  id INT NOT NULL AUTO_INCREMENT,

  person_id INT NOT NULL,
  address_id INT NOT NULL,
  priority INT NOT NULL DEFAULT 0,

  PRIMARY KEY (id),
  FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE,
  FOREIGN KEY (address_id) REFERENCES contact_address(id) ON DELETE CASCADE
);


CREATE TABLE product (
  id INT NOT NULL AUTO_INCREMENT,

  name VARCHAR(100),
  description TEXT,
  -- no foto...

  PRIMARY KEY (id)
);


CREATE TABLE producer (
  id INT NOT NULL AUTO_INCREMENT,

  name VARCHAR(100),
  description TEXT,
  account_id INT NOT NULL,
  -- TODO: blog

  PRIMARY KEY (id)
);

CREATE TABLE producer_person (
  id INT NOT NULL AUTO_INCREMENT,
  producer_id INT NOT NULL,
  person_id INT NOT NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (producer_id) REFERENCES producer(id) ON DELETE CASCADE,
  FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE
);

CREATE TABLE producer_product (
  id INT NOT NULL AUTO_INCREMENT,
  producer_id INT NOT NULL,
  product_id INT NOT NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (producer_id) REFERENCES producer(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE
);


create table turn (
  id INT NOT NULL AUTO_INCREMENT,


  turn_date date not null,
  delivery_place_id int not null,
  person_id int not null,
  work_type char(100), -- testo libero: apertura, consegna...

  PRIMARY KEY (id)
);


--  descrizione
--  a-unit√†: prezzo unitario
--  a-peso: prezzo peso (eg. formaggio)


ordine-singolo-produttore
  produttore
  partecipanti
   persona


--create table cassa (
--  id INT NOT NULL AUTO_INCREMENT,

--  description text,
--
--  PRIMARY KEY (id)
--);


CREATE TABLE account (
  id INT NOT NULL AUTO_INCREMENT,

  state CHAR(1) NOT NULL DEFAULT 'O', -- (O)pen, (C)losing, close(D), (F)usion pending

--  cassa_id int not null,
--  saldo CURRENCY not null, -- magari si calcola con una join?
-- perché potrei avere problemi di concorrenza

  PRIMARY KEY (id)
);

CREATE TABLE account_person (
  -- una volta che una persona diventa intestataria di un conto si crea
  -- una riga qui, con from_date che √® la data da cui inizia l'intestazione
  -- se la persona cambia conto, qui si registra in to_date la data in cui
  -- smette di essere intestataria
  -- quindi l'intestazione √® valida, cio√® si pu√≤ addebitare sul conto,
  -- solo se to_date √® null
  -- mantengo la storicizzazione per poter mostrare alle persone la loro
  -- storia di movimenti non solo limitatamente all'ultimo conto di cui
  -- sono intestatari

  id INT NOT NULL AUTO_INCREMENT,

  from_date DATETIME NOT NULL,
  to_date DATETIME,
  person_id INT NOT NULL,
  account_id INT NOT NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (person_id) REFERENCES person(id),
  FOREIGN KEY (account_id) REFERENCES account(id)
);

CREATE TABLE account_request (
  -- Quando una persona richiede la cointestazione di un conto
  -- creo una riga qui per ogni intestatario.
  -- Se tutti danno l'assenso (Y) o smettono di essere intestatari (U)
  -- allora do accesso, cioè cancello tutte le account_request e creo
  -- una account_person.

  id INT NOT NULL AUTO_INCREMENT,

  account_id INT NOT NULL, -- Recuperabile da account_owner_id ma meglio duplicarlo.
  requester_id INT NOT NULL,
  account_owner_id INT NOT NULL,
  use_granted CHAR(1) NOT NULL DEFAULT 'X', -- (X)tobeanswered, (Y)es, (N)o, (U)nnecessary anymore (requester not owner anymore)

  PRIMARY KEY (id),
  UNIQUE (requester_id), -- una persona può richiedere accesso ad un conto alla volta
  FOREIGN KEY (account_id) REFERENCES account(id),
  FOREIGN KEY (requester_id) REFERENCES person(id),
  FOREIGN KEY (account_owner_id) REFERENCES person(id)
);

CREATE TABLE transaction (
  -- Una transazione è uno spostamento di denaro da un conto all'altro.
  -- Qui però si gestiscono le "split transactions" con la regola che
  -- la sommatoria delle transaction_line.amount di una transaction deve essere 0.
  -- Quindi una transazione "standard" da partita doppia classica avrà
  -- due transaction_line, com amount opposti mentre più in generale le split
  -- avranno un numero di line > 2, ma i totali saranno comunque sempre 0.

  id INT NOT NULL AUTO_INCREMENT,

--  cassa_id int not null,
  description VARCHAR(200),
  transaction_date DATETIME NOT NULL,

  -- Le transazioni e le loro line sono oggetti write once / read only.
  -- Modificare una transazione significa creare una nuova transazione con
  -- i dati modificati e marcare la vecchia come sovrascritta/sostituita
  -- dalla nuova.
  -- Qualsiasi modifica, la descrizione di una line, il suo mount, etc.
  -- produce una transazione completamente nuova.
  -- Questo aumenta lo spazio richiesto ma mantiene lo schema del db più
  -- semplice.
  -- In alternativa si puà fare che le line possono sovrascriversi
  -- DECIDERLO PIÙ TARDI
  -- Per cancellare una transazione se ne crea una senza line.
  modified_by_id INT, -- fk alla transazione che sovrascrive (annullando) questa

  PRIMARY KEY (id),
  FOREIGN KEY (modified_by_id) REFERENCES transaction(id)
);

CREATE TABLE transaction_line (
  id INT NOT NULL AUTO_INCREMENT,

  transaction_id INT NOT NULL,
  account_id INT NOT NULL,
  description VARCHAR(200),
  amount DECIMAL(15,2) NOT NULL, -- currency

  PRIMARY KEY (id),
  FOREIGN KEY (transaction_id) REFERENCES transaction(id),
  FOREIGN KEY (account_id) REFERENCES account(id)
);

CREATE TABLE transaction_log (
  id INT NOT NULL AUTO_INCREMENT,

--  cassa_id int not null,
  log_date DATETIME NOT NULL,
  operator_id INT NOT NULL,

  op_type CHAR(1) NOT NULL, -- (A)dded, (D)eleted, (M)odified
  transaction_id INT NOT NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (operator_id) REFERENCES person(id),
  FOREIGN KEY (transaction_id) REFERENCES transaction(id)
);




create table  (
  id INT NOT NULL AUTO_INCREMENT,


  PRIMARY KEY (id)
);

todo:
gli ordini
agganciare le transazioni agli ordini
contestazione delle transazioni
ma ci deve essere lo stato dell'account:
 * raccomandato da
 * valori di limite (sulla cassa, tipo soglie pre acquisto)
