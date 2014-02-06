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

  UNIQUE (iso3),
  PRIMARY KEY (id)
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

  FOREIGN KEY (state_id) REFERENCES state(id),
  PRIMARY KEY (id)
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

  FOREIGN KEY (city_id) REFERENCES city(id),
  PRIMARY KEY (id)
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

CREATE TABLE person (
  id INT NOT NULL AUTO_INCREMENT,

  first_name VARCHAR(100),
  middle_name VARCHAR(100),
  last_name VARCHAR(100),
  default_delivery_place_id INT,
  address_id INT,
  current_account_id INT,
  cash_treshold DECIMAL(15,2) NOT NULL DEFAULT 0,

  FOREIGN KEY (address_id) REFERENCES street_address(id),
  -- TODO: FOREIGN KEY (current_account_id) REFERENCES account(id)
  PRIMARY KEY (id)
);

CREATE TABLE person_contact (
  id INT NOT NULL AUTO_INCREMENT,

  person_id INT NOT NULL,
  address_id INT NOT NULL,
  priority INT NOT NULL DEFAULT 0,

  FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE,
  FOREIGN KEY (address_id) REFERENCES contact_address(id) ON DELETE CASCADE,
  PRIMARY KEY (id)
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

  FOREIGN KEY (producer_id) REFERENCES producer(id) ON DELETE CASCADE,
  FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE,
  PRIMARY KEY (id)
);

CREATE TABLE producer_product (
  id INT NOT NULL AUTO_INCREMENT,
  producer_id INT NOT NULL,
  product_id INT NOT NULL,

  FOREIGN KEY (producer_id) REFERENCES producer(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
  PRIMARY KEY (id)
);


create table turn (
  id INT NOT NULL AUTO_INCREMENT,


  turn_date date not null,
  delivery_place_id int not null,
  person_id int not null,
  work_type char(100), -- testo libero: apertura, consegna...

  PRIMARY KEY (id)
);


CREATE TABLE product_order (
  -- Tabella principale degli ordini. Un record per ogni ordine.

  id INT NOT NULL AUTO_INCREMENT,
  state CHAR(1) NOT NULL DEFAULT 'D', -- (D)raft, (O)pen, (C)losed, (P)roducers contacted, in deliver(Y), (A)rchivied, cancelled/(S)uspended
  placements_closing DATETIME,
  placements_closed DATETIME, -- quando effettivamente sono passato da O a C
  name VARCHAR(100),
  notes TEXT,

  PRIMARY KEY (id)
);

CREATE TABLE order_supplier (
  -- Produttore che partecipa all'ordine.
  -- I produttori rispetto all'ordine a cui partecipano sono uniformi, cioè:
  -- vendono gli stessi prodotti allo stesso prezzo.
  -- Però non è detto che tutti i produttori producano tutti i prodotti inclusi nell'ordine.
  -- Le specificità riguardano solo i punti di consegna e i tempi.

  id INT NOT NULL AUTO_INCREMENT,
  order_id INT NOT NULL,
  supplier_id INT NOT NULL,

  FOREIGN KEY (order_id) REFERENCES product_order(id) ON DELETE CASCADE,
  FOREIGN KEY (supplier_id) REFERENCES producer(id),
  PRIMARY KEY (id)
);

CREATE TABLE order_supplier_delivery_place (
  -- Dove consegna ciascun fornitore?
  -- TODO: come si modellano i delivery place a staffetta? Cioè quelli dove il produttore non consegna
  -- ma la roba ci viene smistata dalla gente? Si fa che si mette il suppler a NULL e negli assistant
  -- si dice che loro fanno staffetta?

  id INT NOT NULL AUTO_INCREMENT,
  order_supplier_id INT NOT NULL,
  delivery_place_id INT NOT NULL,
  -- È possibile che la consegna sia articolata al punto che lo stesso produttore
  -- può dare date specifiche per ogni punto di consegna.
  supplier_deliver_at DATETIME, -- Orario dell'appuntamento con il fornitore per scaricare la merce.
  delivery_start DATETIME, -- Intervallo di consegna dei prodotti.
  delivery_end DATETIME,
  notes TEXT,

  UNIQUE (order_supplier_id, delivery_place_id),
  FOREIGN KEY (order_supplier_id) REFERENCES order_supplier(id) ON DELETE CASCADE,
  FOREIGN KEY (delivery_place_id) REFERENCES delivery_place(id) ON DELETE CASCADE,
  PRIMARY KEY (id)
);

CREATE TABLE order_supplier_delivery_assistant (
  -- Chi gestisce l'ordine? E quale funzione svolge?
  -- Specifico della coppia produttore / punto di consegna.

  id INT NOT NULL AUTO_INCREMENT,
  delivery_place_id INT NOT NULL,
  producer_check CHAR(1) NOT NULL DEFAULT 'N', -- Y/N, controllo che il produttore abbia consegnato esattamente quanto ordinato
  customer_check CHAR(1) NOT NULL DEFAULT 'N', -- Y/N, controllo che chi ha ordinato ritiri quello che ha ordinato
  delivery_place_opening CHAR(1) NOT NULL DEFAULT 'N', -- Y/N, apertura del punto di consegna
  delivery_place_closing CHAR(1) NOT NULL DEFAULT 'N', -- Y/N, chiusura del punto di consegna
  --staffetta Y/N (vedi TODO in order_supplier_delivery_place)

  FOREIGN KEY (delivery_place_id) REFERENCES order_supplier_delivery_place(id),
  PRIMARY KEY (id)
);

CREATE TABLE order_product (
  -- Qui si specifica quali prodotti sono acquistabili in un dato ordine.
  -- Non è detto che siano tutti i prodotti dei produttori coinvolti, spesso è
  -- un sottoinsieme.
  id INT NOT NULL AUTO_INCREMENT,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  notes TEXT,

  selling_mode CHAR(1) NOT NULL DEFAULT 'U', -- (U)nit, (W)eight
  -- Il campo package_size serve per gestire il caso "pancali", ovvero quando si vende per unità e gli ordini
  -- devono essere multipli interi di un certo numero. Ad esempio, un pancale sono 42 casse di arance e gli ordini
  -- devono essere quindi multipli di 42. Quindi nel caso siano richieste 45 casse, 3 non saranno ordinate e non arriveranno.
  package_size INT NOT NULL DEFAULT 1,
  minimum_quantity INT NOT NULL DEFAULT 0, -- si mette? ha senso?
  maximum_quantity INT,

  FOREIGN KEY (order_id) REFERENCES product_order(id),
  FOREIGN KEY (product_id) REFERENCES product(id),
  PRIMARY KEY (id)
);


CREATE TABLE order_placement (
  -- Parte di una ordinazione. Quando un cliente piazza un'ordinazione, si compila
  -- una riga in questa tabella per ogni prodotto coinvolto nell'ordine.
  id INT NOT NULL AUTO_INCREMENT,
  customer_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 0,
  -- L'ordinazione è Draft finché il cliente non la finalizza. A quel punto diventa
  -- Valid se è stata piazzata in tempo (cioè se product_order.placements_closed è successiva a placement_date)
  -- e se rispetta altri criteri. Altrimenti diventa Out of time nel primo caso o Invalid nell'altro.
  -- I criteri di invalidità sono svariati: pancale non riempito, referente dell'ordine che la marca per altri fattori, etc.
  state CHAR(1) NOT NULL DEFAULT 'D', -- (D)raft, (V)alid, (I)nvalid, (O)ut of time

  -- In ogni ordine ho una riga di transazione per ogni ordinazione di singolo prodotto. Questo è diverso da come si usa GnuCash
  -- dove ho una riga per ogni ordinazione complessiva di tutti i prodotti. Avere un livello di dettaglio simile può
  -- complicare il resoconto e sarebbe ingestibile a mano, ma in una piattaforma automatizzata è più semplice e permette
  -- di gestire meglio le modifiche post consegna anche nell'ottica di gestire le modifiche alle transazioni linea per linea
  -- e non complessivamente.
  transaction_line_id INT,

  -- TODO: qui si agganciano le note/contestazioni

  placement_date DATETIME NOT NULL,
  last_modified DATETIME NOT NULL,

  -- TODO: FOREIGN KEY (transaction_id) REFERENCES transaction_line(id),
  FOREIGN KEY (customer_id) REFERENCES person(id),
  FOREIGN KEY (product_id) REFERENCES order_product(id),
  UNIQUE (customer_id, product_id),
  PRIMARY KEY (id)
);


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

  FOREIGN KEY (person_id) REFERENCES person(id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  PRIMARY KEY (id)
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

  UNIQUE (requester_id), -- una persona può richiedere accesso ad un conto alla volta
  FOREIGN KEY (account_id) REFERENCES account(id),
  FOREIGN KEY (requester_id) REFERENCES person(id),
  FOREIGN KEY (account_owner_id) REFERENCES person(id),
  PRIMARY KEY (id)
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

  FOREIGN KEY (modified_by_id) REFERENCES transaction(id),
  PRIMARY KEY (id)
);

CREATE TABLE transaction_line (
  id INT NOT NULL AUTO_INCREMENT,

  transaction_id INT NOT NULL,
  account_id INT NOT NULL,
  description VARCHAR(200),
  amount DECIMAL(15,2) NOT NULL, -- currency

  FOREIGN KEY (transaction_id) REFERENCES transaction(id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  PRIMARY KEY (id)
);

CREATE TABLE transaction_log (
  id INT NOT NULL AUTO_INCREMENT,

--  cassa_id int not null,
  log_date DATETIME NOT NULL,
  operator_id INT NOT NULL,

  op_type CHAR(1) NOT NULL, -- (A)dded, (D)eleted, (M)odified
  transaction_id INT NOT NULL,

  FOREIGN KEY (operator_id) REFERENCES person(id),
  FOREIGN KEY (transaction_id) REFERENCES transaction(id),
  PRIMARY KEY (id)
);




CREATE TABLE csa (
  -- Una comunità. Le persone possono partecipare a più comunità.
  -- La partecipazione è indicata dai permessi (membership).

  id INT NOT NULL AUTO_INCREMENT,

  -- Cassa comune
  kitty_id INT NOT NULL,
  -- Quanto versano, ogni anno, i partecipanti del gas in cassa comune
  -- TODO: gestire il caso di persone che appartengano a più gas: magari versano in un gas solo? O un po' in tutti?
  annual_kitty_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
  -- Soglia di default per i nuovi arrivati
  default_account_treshold DECIMAL(15,2) NOT NULL DEFAULT 0,

  FOREIGN KEY (kitty_id) REFERENCES account(id),
  PRIMARY KEY (id)
);

CREATE TABLE permission (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(32) NOT NULL,
  description TEXT,
  visibility INT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

INSERT INTO permission (name, visibility) VALUES ('membership', 10);
INSERT INTO permission (name, visibility) VALUES ('canPlaceOrders', 50);
INSERT INTO permission (name, visibility) VALUES ('canEditTurns', 100);
-- Creare account significa in sostanza raccomandare nuovi membri nella comunità.
-- Farlo significa dichiarare che si conosce personalmente e che la persona è affidabile.
INSERT INTO permission (name, visibility) VALUES ('canCreateAccounts', 200);
INSERT INTO permission (name, visibility) VALUES ('canModifyPeopleAccounts', 2000);
INSERT INTO permission (name, visibility) VALUES ('canEditProducers', 1000);
INSERT INTO permission (name, visibility) VALUES ('canEditProducts', 1500);
--INSERT INTO permission (name, visibility) VALUES ('', 2);
--INSERT INTO permission (name, visibility) VALUES ('', 2);

CREATE TABLE permission_grant (
  id INT NOT NULL AUTO_INCREMENT,

  csa_id INT NOT NULL,
  person_id INT NOT NULL,
  perm_id VARCHAR(32) NOT NULL,

  -- I permessi sono specifici di un csa. La stessa persona può avere
  -- diritti diversi su csa diversi.
  UNIQUE (csa_id, person_id, perm_id),
  PRIMARY KEY (id)
);


-- resoconti sugli ordini:
-- * commenti sui prodotti
-- * valutazioni personali o pubbliche
--   nb: i commenti sui prodotti sono locali all'ordine perché variano da ordine a ordine
--   (esempio principe: le arance, mentre altri prodotti sono uniformi: farine, uova, etc.)
