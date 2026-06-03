# Brewery Digital Twin

Ένα mini βιομηχανικό digital twin για παρακολούθηση διεργασιών ζυθοποιείου.
Δεδομένα αισθητήρων ρέουν από ανεξάρτητα gateways σε ένα time-series backend που
αποθηκεύει τις ωμές μετρήσεις, εντοπίζει τιμές εκτός προδιαγραφών, και υπολογίζει
λειτουργικά KPIs (μεταξύ άλλων το OEE). Όλο το σύστημα — βάση, API, simulator —
σηκώνεται με μία εντολή.

## Αρχιτεκτονική

Layered σχεδίαση όπου κάθε επίπεδο μιλάει μόνο στο αμέσως από κάτω του:

```
Sensor Simulator  (scripts/simulator.py)   -- ανεξάρτητος HTTP client
        |  HTTP POST (httpx)
        v
API Layer  (main.py)                        -- routing, Pydantic validation
        |
        v
Service Layer  (service.py)                 -- business logic, KPIs, OEE
        |
        v
Data Layer  (database.py)                   -- το μόνο layer που αγγίζει τη βάση
        |  psycopg
        v
TimescaleDB (PostgreSQL + time-series)      -- raw measurements + tanks + batches
```

Ο διαχωρισμός κρατά τη business logic testable χωρίς βάση, και περιορίζει τον
DB-specific κώδικα σε ένα layer — αν αλλάξει η βάση, πειράζεται μόνο το data layer.

## Tech stack

| Component     | Επιλογή             |
| ------------- | ------------------- |
| Γλώσσα        | Python 3.11         |
| API framework | FastAPI             |
| Validation    | Pydantic            |
| Database      | TimescaleDB (PG 16) |
| DB driver     | psycopg 3           |
| HTTP client   | httpx               |
| Frontend      | HTML + Chart.js     |
| Testing       | pytest              |
| Infra         | Docker Compose      |

## Εκτέλεση

Προαπαιτούμενα: Docker Desktop.

```bash
cp .env.example .env        # συμπλήρωσε τα credentials
docker compose up --build
```

- API & dashboard: `http://127.0.0.1:8000/`
- Interactive API docs (Swagger): `http://127.0.0.1:8000/docs`

Το schema και τα seed data εφαρμόζονται αυτόματα στην πρώτη εκκίνηση.

## API

| Method | Endpoint                | Περιγραφή                                   |
| ------ | ----------------------- | ------------------------------------------- |
| GET    | `/`                     | Live dashboard                              |
| GET    | `/health`               | Liveness check                              |
| POST   | `/measurements`         | Καταχώρηση μέτρησης (με validation)         |
| GET    | `/tanks/{id}/stats`     | avg / min / max σε χρονικό παράθυρο         |
| GET    | `/tanks/{id}/anomalies` | Μετρήσεις εκτός των ορίων του ενεργού batch |
| GET    | `/tanks/{id}/oee`       | Εκτίμηση OEE                                |

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Καλύπτουν καθαρή λογική (random walk + mean reversion του simulator) και business
logic (υπολογισμός OEE, με mocking του data layer ώστε να τεστάρεται χωρίς βάση).

## Αρχιτεκτονικές Αποφάσεις

**Raw measurements ως single source of truth.** Αποθηκεύονται οι ωμές μετρήσεις, όχι
έτοιμα KPIs. Τα KPIs υπολογίζονται από τα raw — έτσι είναι recomputable: νέο KPI ή
διόρθωση τύπου εφαρμόζεται σε όλο το ιστορικό. Κρατούνται προ-υπολογισμένα aggregates
για ταχύτητα, αλλά ποτέ ως μοναδική πηγή.

**Narrow/long μορφή για τις μετρήσεις** (`sensor_type` + `value`). Νέος τύπος αισθητήρα
δεν χρειάζεται αλλαγή schema — μόνο νέα τιμή στο enum. Βασικό για επεκτασιμότητα σε IIoT.

**Tanks vs Batches.** Τα όρια (π.χ. θερμοκρασίας) ανήκουν στο `batch`, όχι στο `tank`,
γιατί η ίδια δεξαμενή βράζει διαφορετικά προϊόντα σε διαφορετικές περιόδους — καθένα με
δικές του προδιαγραφές. Μία δεξαμενή έχει πολλά batches (1:N, με foreign key
`batches.tank_id -> tanks.id`). Το hypertable των measurements σκόπιμα δεν έχει foreign
key, ώστε το high-volume ingestion να μένει γρήγορο.

**OEE = Availability × Performance × Quality (πολλαπλασιαστικό).** Ένας μηδενικός
παράγοντας (π.χ. δεξαμενή εξ ολοκλήρου εκτός προδιαγραφών -> Quality = 0) σωστά μηδενίζει
ολόκληρο το OEE — κάτι που ο μέσος όρος θα έκρυβε. Το Performance είναι τεκμηριωμένο
placeholder (απαιτεί production-rate counters που τα sensor data δεν παρέχουν).

**Security από την αρχή.** Secrets σε `.env` (git-ignored, με `.env.example` ως
υπόδειγμα), parameterized queries παντού (καμία string concatenation από user input),
και transactions με commit-on-success / rollback-on-error / guaranteed close.

## Project layout

```
src/brewery_twin/    # application package (main, service, database, models, config, simulation)
scripts/simulator.py # standalone sensor simulator
db/                  # schema.sql + seed.sql
tests/               # pytest suite
docker-compose.yml   # db + api + simulator
Dockerfile
```

## Μελλοντικές επεκτάσεις

- Connection pooling για υψηλότερο ingestion throughput
- Γενικευμένο anomaly detection για όλους τους τύπους αισθητήρων
- Πλήρης υπολογισμός Performance στο OEE με production-rate counters
- Διαχείριση batch lifecycle (έναρξη/λήξη παρτίδων)