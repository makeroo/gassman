-- version 10

SET SESSION storage_engine = "MyISAM";
SET SESSION time_zone = "+0:00";
ALTER DATABASE CHARACTER SET "utf8";

CREATE TABLE currency (
  id INT NOT NULL AUTO_INCREMENT,
  iso_4217 CHAR(3),
  symbol VARCHAR(4) NOT NULL,
  description TEXT,

  PRIMARY KEY (id)
);

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
  -- questa è la provincia
  state varchar(10),
  -- e questa è la nazione
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
  -- nb: lo stato Lo recupero dalla città.
  description TEXT, -- Note aggiuntive per raggiungere la persona, eg. "Suonare XXX".

  FOREIGN KEY (city_id) REFERENCES city(id),
  PRIMARY KEY (id)
);

CREATE TABLE contact_address (
  id INT NOT NULL AUTO_INCREMENT,
  address VARCHAR(100), -- Il numero del telefono, l'indirzzo email, etc.
  kind CHAR(1) NOT NULL DEFAULT 'M', -- (T)elephone, (M)obile, (E)mail, (F)ax, (I)d, (N)ickname
  contact_type VARCHAR(20), -- Testo libero: cell, ufficio, casa...

  PRIMARY KEY (id)
);



CREATE TABLE delivery_place (
  -- punto di consegna

  id INT NOT NULL AUTO_INCREMENT,
  address_id INT NOT NULL,
  description TEXT,

  FOREIGN KEY (address_id) REFERENCES street_address(id),
  PRIMARY KEY (id)
);



CREATE TABLE csa (
  -- Una comunità. Le persone possono partecipare a più comunità.
  -- La partecipazione è indicata dai permessi (membership).

  id INT NOT NULL AUTO_INCREMENT,

  name VARCHAR(255),
  description TEXT,

  -- Soglia di default per i nuovi arrivati
  default_account_threshold DECIMAL(15,2) NOT NULL DEFAULT 0,
  -- Conto per le uscite (finché si rimane al modello salvadenaio...)
  -- expenses_id INT NOT NULL,
  -- Conto per le entrate (finché si rimane al modello salvadenaio, poi scompare)
  -- income_id INT NOT NULL,

--  FOREIGN KEY (kitty_id) REFERENCES account(id),
--  FOREIGN KEY (expenses_id) REFERENCES account(id),
--  FOREIGN KEY (income_id) REFERENCES account(id),
  PRIMARY KEY (id)
);



CREATE TABLE account (
  -- ATTENZIONE: non sono ammessi conti con id 0 (vedi save transaction di tipo payment)
  id INT NOT NULL AUTO_INCREMENT,

  state CHAR(1) NOT NULL DEFAULT 'O', -- (O)pen, (C)losing, close(D), (F)usion pending

  csa_id INT NOT NULL,
  currency_id INT NOT NULL,

  -- Cassa comune
  -- Quanto versano, ogni anno, i partecipanti del gas in cassa comune
  -- TODO: gestire il caso di persone che appartengano a più gas: magari versano in un gas solo? O un po' in tutti?
  membership_fee DECIMAL(15,2) NOT NULL DEFAULT 0,

--  cassa_id int not null,
--  saldo CURRENCY not null, -- magari si calcola con una join?
-- perché potrei avere problemi di concorrenza

  -- colonne destinate a sparire, usate solo per il periodo di transizione gnucash
  -- gc_type può valere:
  -- ASSET: i membri della comunità + cassa comune (lucca ha anche Attività e Scomparsi)
  -- EXPENSE: le spese (lucca ha una gerarchia che non userò più)
  -- ROOT: una radice, non la userò più (retaggio gnucash)
  -- EQUITY: capitali, bilanci d'apertura, non li userò più (retaggio gnucash)
  -- INCOME: versamenti
  -- BANK: sbilancio eur, orfano eur, non li userò più (retaggio gnucash)
  -- in realtà a me un tipo serve: Expenses, Income, Asset e Kitty (Asset)
  -- gc_id CHAR(32),
  gc_name VARCHAR(255),
  -- gc_desc VARCHAR(255),
  gc_type VARCHAR(255),
  -- gc_parent CHAR(32),

  -- UNIQUE (gc_id),
  FOREIGN KEY (csa_id) REFERENCES csa(id),
  FOREIGN KEY (currency_id) REFERENCES currency(id),
  PRIMARY KEY (id)
);


CREATE TABLE person (
  id INT NOT NULL AUTO_INCREMENT,

  first_name VARCHAR(100),
  middle_name VARCHAR(100),
  last_name VARCHAR(100),
  default_delivery_place_id INT,
  address_id INT,
  cash_treshold DECIMAL(15,2) NOT NULL DEFAULT 0,
  rss_feed_id CHAR(64),

  account_notifications CHAR(1) NOT NULL DEFAULT 'E', -- Every movement, Dayly, Weekly, Never

  FOREIGN KEY (address_id) REFERENCES street_address(id),
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


CREATE TABLE permission (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(32) NOT NULL,
  description TEXT,
  visibility INT NOT NULL DEFAULT 0,
  ord INT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE permission_grant (
  id INT NOT NULL AUTO_INCREMENT,

  csa_id INT NOT NULL,
  person_id INT NOT NULL,
  perm_id INT NOT NULL,

  -- I permessi sono specifici di un csa. La stessa persona può avere
  -- diritti diversi su csa diversi.
  UNIQUE (csa_id, person_id, perm_id),
  FOREIGN KEY (csa_id) REFERENCES csa(id),
  FOREIGN KEY (person_id) REFERENCES person(id),
  FOREIGN KEY (perm_id) REFERENCES permission(id),
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
  -- Per cancellare una transazione se ne crea una senza line.
  modified_by_id INT,

  -- gc_id CHAR(32),
  -- tipi di transazione:
  -- (g)nucash/generic
  -- (d)eposit
  -- (p)ayment implica il tipo di form presentato dal sito
  -- (t)rashed cestinata, significa che non ha linee
  -- (u)nfinished (ie. draft): è in corso di salvataggio
  -- (e)rror: è stato richiesto il salvataggio di una transazione, ma i dati non sono corretti
  --          eg. account non appartenenti al csa indicato, o monete non uniformi
  cc_type CHAR(1) NOT NULL DEFAULT 'G',

  -- la currency la posso dedurre dai conti, perché deve essere
  -- coerente, cioè i conti coinvolti in una transazione devono avere
  -- la stessa moneta, ma la riporto qua ugualmente:
  -- 1) riduco banda / query
  -- 2) la uso per verificare la coerenza
  currency_id INT NOT NULL,

  -- idem per currency, ho bisogno di avere qua la csa senza passare dalle line
  -- tanto più nel caso di una transaction_log deleted per cui per sapere il csa
  -- devo passare dalla transaction cancellata
  csa_id INT NOT NULL,

  -- UNIQUE (gc_id), -- non è unico a causa del rewrite!
  FOREIGN KEY (currency_id) REFERENCES currency(id),
  FOREIGN KEY (csa_id) REFERENCES csa(id),
  PRIMARY KEY (id)
);

ALTER TABLE transaction ADD FOREIGN KEY (modified_by_id) REFERENCES transaction(id);

CREATE TABLE transaction_line (
  id INT NOT NULL AUTO_INCREMENT,

  transaction_id INT NOT NULL,
  account_id INT NOT NULL,
  description VARCHAR(200),
  amount DECIMAL(15,2) NOT NULL, -- currency

  -- gc_id CHAR(32),

  -- UNIQUE (gc_id), -- non è unico a causa del rewrite!
  FOREIGN KEY (transaction_id) REFERENCES transaction(id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  PRIMARY KEY (id)
);

CREATE TABLE transaction_log (
  id INT NOT NULL AUTO_INCREMENT,

--  cassa_id int not null,
  log_date DATETIME NOT NULL,
  operator_id INT NOT NULL,

  op_type CHAR(1) NOT NULL, -- (A)dded, (D)eleted, (M)odified, (E)rror
  transaction_id INT NOT NULL,
  notes TEXT, -- in caso di errore, il motivo

  FOREIGN KEY (operator_id) REFERENCES person(id),
  FOREIGN KEY (transaction_id) REFERENCES transaction(id),
  PRIMARY KEY (id)
);


CREATE TABLE producer (
  id INT NOT NULL AUTO_INCREMENT,

  name VARCHAR(100),
  description TEXT,
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
