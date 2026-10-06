# QuestDB Jev Signals

Install the live TLS dependency / Installez la dépendance TLS pour l'usage réel / Instale la dependencia TLS para uso real: `python3 -m pip install -r requirements.txt`.

## English

Materialize a versioned Jev decision for each distinct log template before querying it in QuestDB. The Python CLI reads JSONL rows with a `template` string, hashes the template, classifies it once per policy version, and emits QuestDB InfluxDB Line Protocol for a `jev_signals` table. It never writes raw log text to QuestDB. Decisions below 0.90 confidence become `review`.

Offline run: `python3 signals.py examples/templates.jsonl --fixtures examples/fixtures.json`. Tests: `python3 -m unittest discover -s tests -v`. For live publishing, set `TYPESAFE_API_KEY` and `QUESTDB_WRITE_URL` privately, then run `python3 signals.py examples/templates.jsonl --push --state .local/state.sqlite`. The write URL must end in `/write` and use HTTPS, or localhost HTTP. This CLI uses the documented ILP/HTTP compatibility endpoint. A production connector should use QuestDB's current native client and a durable source queue. SQLite records successful publishes to avoid repeat decisions; a crash after QuestDB accepts a row but before SQLite commits can still produce a duplicate. The Jev API was exercised with synthetic input; no live QuestDB instance was available.

## Français

Matérialisez dans QuestDB une décision Jev versionnée pour chaque modèle de log distinct. Le programme lit des lignes JSONL avec le champ `template`, calcule son empreinte, le classe une fois par version de politique et produit le protocole InfluxDB Line Protocol pour la table `jev_signals`. Le texte brut du log n'est jamais écrit dans QuestDB. Une probabilité inférieure à 0,90 produit `review`.

Exemple hors ligne : `python3 signals.py examples/templates.jsonl --fixtures examples/fixtures.json`. Tests : `python3 -m unittest discover -s tests -v`. Pour publier, définissez `TYPESAFE_API_KEY` et `QUESTDB_WRITE_URL` dans un environnement privé, puis lancez `python3 signals.py examples/templates.jsonl --push --state .local/state.sqlite`. L'URL doit se terminer par `/write` et utiliser HTTPS ou HTTP local. Le programme utilise l'interface de compatibilité ILP/HTTP ; un connecteur de production devrait employer le client natif actuel et une file source durable. SQLite mémorise les publications réussies, mais un arrêt entre l'acceptation par QuestDB et l'enregistrement SQLite peut créer un doublon. L'API Jev a été testée avec des données synthétiques ; aucune instance QuestDB réelle n'était disponible.

## Español

Materialice en QuestDB una decisión Jev versionada para cada plantilla de registro distinta. El programa lee líneas JSONL con el campo `template`, calcula su huella, la clasifica una vez por versión de política y emite InfluxDB Line Protocol para la tabla `jev_signals`. Nunca escribe el texto original del registro en QuestDB. Una probabilidad inferior a 0,90 produce `review`.

Ejemplo sin conexión: `python3 signals.py examples/templates.jsonl --fixtures examples/fixtures.json`. Pruebas: `python3 -m unittest discover -s tests -v`. Para publicar, defina `TYPESAFE_API_KEY` y `QUESTDB_WRITE_URL` en un entorno privado y ejecute `python3 signals.py examples/templates.jsonl --push --state .local/state.sqlite`. La URL debe terminar en `/write` y usar HTTPS o HTTP local. El programa utiliza el endpoint de compatibilidad ILP/HTTP; un conector de producción debería usar el cliente nativo actual y una cola de origen duradera. SQLite recuerda las publicaciones completadas, pero una interrupción entre la aceptación de QuestDB y la confirmación en SQLite puede causar un duplicado. La API Jev se probó con datos sintéticos; no había una instancia QuestDB real disponible.

Source integration reference: [QuestDB ILP/HTTP](https://questdb.com/docs/connect/compatibility/ilp/overview/). License: MIT. Tag: `v0.1.0`.
