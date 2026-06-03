# Brewery Digital Twin

![CI](https://github.com/Mikostis/brewery-digital-twin/actions/workflows/ci.yml/badge.svg)

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
| CI            | GitHub Actions      |
| Infra         | Docker Compose      |

## Εκτέλεση

Προαπαιτούμενα: Docker Desktop.

```bash
# 1. Φτιάξε το .env από το παράδειγμα
cp .env.example .env
#    (Windows PowerShell: copy .env.example .env)

# 2. Σήκωσε τα πάντα
docker compose up --build
```

- API & dashboard: `http://127.0.0.1:8000/`
- Interactive API docs (Swagger): `http://127.0.0.1:8000/docs`

Το schema και τα seed data εφαρμόζονται αυτόματα στην πρώτη εκκίνηση.

### Ρύθμιση `.env`

Τα credentials της βάσης δεν είναι commit-αρισμένα στο repo (το `.env` είναι
git-ignored). Αντίγραψε το `.env.example` σε `.env` — οι τιμές που ορίζεις εκεί
**δημιουργούν** τον χρήστη και τη βάση μέσα στο container την πρώτη φορά, οπότε
μπορούν να είναι οποιεσδήποτε (local-only):

```
POSTGRES_USER=brewery_admin
POSTGRES_PASSWORD=ena_diko_sou_password
POSTGRES_DB=brewery
```

Δεν χρειάζεται εγκατεστημένη PostgreSQL — η βάση τρέχει μέσα σε container.

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
Τρέχουν αυτόματα σε κάθε push μέσω GitHub Actions (βλ. badge στην κορυφή).

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
.github/workflows/   # CI pipeline (GitHub Actions)
docker-compose.yml   # db + api + simulator
Dockerfile
```

## Μελλοντικές επεκτάσεις

- Connection pooling για υψηλότερο ingestion throughput
- Γενικευμένο anomaly detection για όλους τους τύπους αισθητήρων
- Πλήρης υπολογισμός Performance στο OEE με production-rate counters
- Διαχείριση batch lifecycle (έναρξη/λήξη παρτίδων)

Πηγές / References
Οι αρχιτεκτονικές και domain αποφάσεις στηρίχθηκαν σε επίσημη τεκμηρίωση και
καθιερωμένες πηγές του κλάδου.
Domain (ζυθοποιείο / θερμοκρασία ζύμωσης / batches):

Τα όρια θερμοκρασίας ανά προϊόν (γιατί lager/pilsner ζυμώνεται ψυχρά ~7–13 °C ενώ
ale θερμότερα ~18–22 °C — άρα μια Pilsner στους 20 °C είναι εκτός προδιαγραφών):
https://byo.com/articles/fermentation-temperature-control-tips-from-the-pros/ ·
https://homebrewersassociation.org/how-to-brew/understanding-fermentation-temperature-control/
Αυτό τεκμηριώνει την απόφαση τα όρια να ανήκουν στο batch (ανά προϊόν/περίοδο), όχι στο tank.

OEE — γενικός ορισμός & εφαρμογή σε Food & Beverage:

Ορισμός (Availability × Performance × Quality, world-class ~85%):
https://www.oee.com/ · https://en.wikipedia.org/wiki/Overall_equipment_effectiveness
OEE ειδικά στον κλάδο τροφίμων/ποτών (γιατί συχνά εστιάζει σε Availability & Quality):
https://www.vorne.com/solutions/industries/food-and-beverage/ ·
https://www.worximity.com/blog/ways-to-calculate-oee-in-the-food-and-beverage-manufacturing-industry

Tech stack (υλοποίηση):

TimescaleDB hypertables & chunks: https://docs.timescale.com/use-timescale/latest/hypertables/
FastAPI & Pydantic: https://fastapi.tiangolo.com/ · https://docs.pydantic.dev/latest/
psycopg 3 (parameterized queries): https://www.psycopg.org/psycopg3/docs/