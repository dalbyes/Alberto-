# Monitoraggio bandi TED — calzature vigili del fuoco, polizia, soccorso

Programma per cercare e analizzare i bandi di gara pubblici europei
pubblicati su **TED (Tenders Electronic Daily)**, il portale ufficiale UE
degli appalti pubblici, relativi a:

- stivali/calzature per i **vigili del fuoco**
- scarpe/calzature per i **corpi di polizia**
- calzature per il **soccorso** (protezione civile, soccorso alpino, ecc.)
- più in generale calzature **antinfortunistiche/di sicurezza**

## Come funziona

1. Costruisce una query per l'[API di ricerca di TED](https://docs.ted.europa.eu/api/latest/index.html)
   combinando:
   - codici **CPV** (vocabolario comune per gli appalti) relativi a calzature
     protettive e indumenti antincendio/di sicurezza;
   - parole chiave **multilingua** (italiano, inglese, francese, tedesco,
     spagnolo, portoghese) per non perdere bandi classificati in modo
     generico.
2. Scarica i risultati (con paginazione automatica) e li salva in
   `data/notices.csv`, **senza duplicati** (dedup per numero di bando).
3. Classifica ogni bando in una categoria (`vigili_del_fuoco`, `polizia`,
   `soccorso`, `antinfortunistica_generica`, `altro`) in base al titolo.
4. Genera un report (`data/report.md`) con conteggi per categoria/paese/ente
   aggiudicatore e le prossime scadenze.

## Versione Windows (.exe) — nessun Python richiesto

C'è un'interfaccia grafica semplice (`gui.py`: campi per giorni/paesi/modalità,
pulsanti "Cerca su TED" e "Genera report") pensata per essere distribuita
come eseguibile standalone.

**Opzione 1 — scaricare l'eseguibile già compilato (consigliata):**
ad ogni push il workflow GitHub Actions `.github/workflows/build-windows.yml`
compila automaticamente `TED_Calzature.exe` su una macchina Windows reale.
Per scaricarlo: schede *Actions* del repository → ultima esecuzione di
"Build Windows executable" → sezione *Artifacts* → `TED_Calzature-windows`
(contiene il file .exe). Nessuna installazione di Python necessaria.

**Opzione 2 — compilarlo tu stesso su un PC Windows:**

```
build_windows.bat
```

(richiede Python 3.10+ installato una tantum da python.org; lo script crea
un ambiente virtuale, installa le dipendenze e PyInstaller, e genera
`dist\TED_Calzature.exe`). Una volta compilato, l'.exe funziona anche senza
Python installato: puoi copiarlo e lanciarlo con un doppio click.

## Installazione (uso da riga di comando / sviluppo)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

Cercare i bandi pubblicati negli ultimi 30 giorni (tutti i paesi coperti da TED):

```bash
python -m ted_tenders.cli search --days-back 30
```

Filtrare per paesi specifici e usare la modalità "strict" (CPV **e** parola
chiave, meno falsi positivi ma possibile minor copertura):

```bash
python -m ted_tenders.cli search --countries IT,FR,DE,ES --mode strict
```

Vedere la query generata senza interrogare l'API (utile per debug):

```bash
python -m ted_tenders.cli search --dry-run
```

Generare/aggiornare il report dai bandi già salvati:

```bash
python -m ted_tenders.cli report
```

Eseguire più volte `search` (es. ogni giorno via cron) aggiorna
incrementalmente `data/notices.csv` senza creare duplicati.

## Test

```bash
pip install -r requirements-dev.txt
pytest
```

I test coprono query builder, classificazione, storage/dedup, report e
paginazione del client HTTP (con risposte simulate, senza chiamate di rete
reali).

## Limitazioni note / cose da verificare

- **Accesso di rete**: l'API TED (`api.ted.europa.eu`) deve essere
  raggiungibile dall'ambiente in cui esegui `search`. In alcuni ambienti
  sandbox l'accesso a internet è limitato a una lista di host consentiti e
  va abilitato esplicitamente nelle impostazioni di rete dell'ambiente.
- **Codici CPV e nomi dei campi API**: elencati in `ted_tenders/config.py`
  con commenti su cosa verificare. Il nome esatto dei campi della "expert
  query" (es. `buyer-country`, `publication-date`) e la struttura della
  risposta vanno confrontati con la documentazione ufficiale più recente
  (https://docs.ted.europa.eu/api/latest/index.html) prima di un uso
  continuativo, perché l'API è stata scritta qui senza poterla interrogare
  dal vivo. Se un campo non corrisponde, la correzione va fatta in
  `config.py` / `query_builder.py` / `models.py`.
- **Falsi positivi/negativi**: la modalità `broad` (default) privilegia la
  copertura; rivedi manualmente la colonna `category` nel CSV e affina le
  parole chiave in `config.py` secondo necessità.

## Struttura del progetto

```
ted_tenders/
  config.py         # codici CPV, parole chiave, paesi, nomi campi API
  query_builder.py  # costruzione della query TED
  client.py         # chiamate HTTP paginate verso l'API TED
  models.py         # modello Notice e mappatura CSV
  classify.py       # classificazione per categoria
  storage.py        # salvataggio/dedup su CSV
  report.py         # aggregazione e report markdown
  cli.py            # comandi `search` e `report`
tests/              # test unitari (nessuna chiamata di rete reale)
data/               # output: notices.csv, report.md (non versionati)
```
