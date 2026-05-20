# FitTrackee
**A simple self-hosted workout/activity tracker.**  


[![Python Version](https://img.shields.io/pypi/pyversions/fittrackee.svg)](https://python.org)
[![Flask Version](https://img.shields.io/badge/flask-3.1-brightgreen.svg)](http://flask.pocoo.org/) 
[![code formatter: ruff](https://img.shields.io/badge/code%20formatter-ruff-d7ff64)](https://docs.astral.sh/ruff/) 
[![type check: mypy](https://img.shields.io/badge/type%20check-mypy-blue)](http://mypy-lang.org/)  
[![Vue Version](https://img.shields.io/badge/vue-3.5-brightgreen.svg)](https://v3.vuejs.org/) 
[![code formatter: prettier](https://img.shields.io/badge/code%20formatter-prettier-ff69b4.svg)](https://github.com/prettier/prettier) 
[![Typescript Version](https://img.shields.io/npm/types/typescript)](https://www.typescriptlang.org/)  
[![PostgreSQL version](https://img.shields.io/badge/PostgreSQL-14_|_15_|_16_|_17_|_18-336791)](https://www.postgresql.org/) [![PostgreSQL version](https://img.shields.io/badge/PostGIS-3.4_|_3.5_|_3.6-5b7b9f)](https://postgis.net/)  
[![PyPI version](https://img.shields.io/pypi/v/fittrackee?logo=pypi)](https://pypi.org/project/fittrackee/) [![docker image version](https://img.shields.io/docker/v/fittrackee/fittrackee?logo=docker)](https://hub.docker.com/r/fittrackee/fittrackee)  
[![Coverage Status](https://coveralls.io/repos/github/SamR1/FitTrackee/badge.svg?branch=main)](https://coveralls.io/github/SamR1/FitTrackee?branch=main)<sup><sup>1</sup></sup> [![python pipeline status](https://github.com/SamR1/FitTrackee/actions/workflows/.tests-python.yml/badge.svg)](https://github.com/SamR1/FitTrackee/actions/workflows/.tests-python.yml)  [![javascript pipeline status](https://codeberg.org/FitTrackee/FitTrackee/badges/workflows/.javascript-checks-and-tests.yml/badge.svg?branch=main)](https://codeberg.org/FitTrackee/FitTrackee/actions?workflow=.javascript-checks-and-tests.yml)  
[![translation status](https://hosted.weblate.org/widgets/fittrackee/-/svg-badge.svg)](https://hosted.weblate.org/engage/fittrackee/)
[![translation languages](https://hosted.weblate.org/widget/fittrackee/language-badge.svg)](https://hosted.weblate.org/engage/fittrackee/)   
[![Matrix](https://img.shields.io/matrix/fittrackee%3Amatrix.org?logo=matrix)](https://matrix.to/#/#fittrackee:matrix.org)
[![Mastodon Follow](https://img.shields.io/mastodon/follow/109270806934115805?domain=fosstodon.org)](https://fosstodon.org/@FitTrackee)  
---

Web application allowing tracking of outdoor activities (workouts) from files, \
with data on your own server.  

Several mobile apps or devices can store workouts data locally and export them into a file.  
Examples for Android (non-exhaustive list):  
* [FitoTrack](https://codeberg.org/jannis/FitoTrack) (GPLv3)  
* [OpenTracks](https://codeberg.org/OpenTracksApp/OpenTracks) (Apache License)  
* [Runner Up](https://github.com/jonasoreland/runnerup) (GPLv3)  

To get workouts from devices like smartwatches:
* [Amazfish](https://amazfish.github.io/) (Sailfish OS, GPLv3, integration with FitTrackee from v2.9.0)
* [Gadgetbridge](https://gadgetbridge.org) (Android, GPLv3, no integration)

It is also possible to add a workout without a file.

Map data from [OpenStreetMap](https://www.openstreetmap.org).  

## Fork additions: single-user mode

This fork adds quality-of-life features for self-hosted single-user deployments.

### Disable registration

Set the environment variable `REGISTRATION_DISABLED=true` to permanently close
new account sign-ups regardless of the `max_users` admin setting:

```bash
# .env / .env.docker
export REGISTRATION_DISABLED=true
```

- The API returns `403 – registration is disabled` for any registration attempt.
- The `/register` route redirects to `/login` in the frontend.
- The existing `max_users` admin config field continues to work normally when the variable is not set.

### Docker: bootstrap a single user on first start

Set the following environment variables to automatically create an account when
the container starts for the first time. Re-runs are safe — if the user already
exists the command is a no-op:

```bash
# .env.docker
export INIT_USERNAME=alice
export INIT_EMAIL=alice@example.com
export INIT_PASSWORD=changeme
export INIT_ROLE=admin          # owner | admin | moderator | user (default: admin)
```

Pair with `REGISTRATION_DISABLED=true` for a fully locked-down single-user instance.

### Automated GPX / workout file import from a local directory

The `ftcli workouts import_dir` CLI command scans a local directory for workout
files and imports them for a given user and sport — useful for drop-folder
automation with cron or a systemd path unit.

**Supported formats:** GPX, FIT, TCX, KML, KMZ — including `.tcx` files from
Garmin devices, Polar Flow exports, etc.

#### TCX sport inference

For **TCX files** the command reads the `<Activity Sport="...">` attribute from
the file header and maps it to a FitTrackee sport. The default mapping is stored
in `fittrackee/workouts/tcx_sport_mapping.json` and covers the most common TCX
sport values out of the box:

| TCX Sport value | FitTrackee sport |
|-----------------|-----------------|
| Biking | Cycling (Sport) |
| Mountain Biking | Mountain Biking |
| Running | Running |
| Trail Running | Trail |
| Hiking | Hiking |
| Walking | Walking |
| Swimming | Open Water Swimming |
| Cross Country Skiing | Skiing Cross Country |
| Alpine Skiing | Skiing Alpine |
| Rowing | Rowing |
| Kayaking | Kayaking |
| Other | Hiking |

Edit `tcx_sport_mapping.json` to customise the defaults for your instance.
The `--sport-mapping` CLI option lets you override individual entries per run
(merged on top of the file, so you only need to specify what differs).

```
Usage: ftcli workouts import_dir [OPTIONS]

  Import all workout files from a local directory.

  Supported formats: gpx, fit, tcx, kml, kmz.
  Files are processed in alphabetical order.

  For TCX files the sport type is inferred from the <Activity Sport="...">
  attribute when --sport-mapping is provided. --sport-id is used as the
  fallback for files where the sport cannot be determined.

Options:
  --dir DIRECTORY          Directory containing workout files to import.
                           [required]
  --sport-id INTEGER       Default sport id for imported workouts. Used when
                           sport cannot be inferred from the file (required
                           for non-TCX formats).
  --sport-mapping TEXT     Comma-separated TCX sport → FitTrackee sport
                           overrides (merged on top of tcx_sport_mapping.json).
                           Values can be sport IDs or labels. Example:
                             "Biking:Mountain Biking,Other:Walking"
                           If omitted the bundled default file is used.
  --username TEXT          Username to import workouts for. Defaults to the
                           only active user when just one exists.
  --on-success [keep|move|delete]
                           Action after a successful import: 'keep' leaves the
                           file in place, 'move' moves it to a done/
                           subdirectory, 'delete' removes it.  [default: keep]
  -v, --verbose            Enable verbose output log.
```

At least one of `--sport-id` or `--sport-mapping` must be provided. Files
whose sport cannot be resolved are skipped with an error (counted in the final
summary).

**Look up sport IDs / labels** for your instance via the FitTrackee API:

```bash
# No auth required
curl http://localhost:5000/api/sports

# In Docker
docker compose exec fittrackee curl http://localhost:5000/api/sports
```

Default sports after a fresh install (IDs may differ on your instance):

| ID | Label |
|----|-------|
| 1  | Cycling (Sport) |
| 2  | Cycling (Transport) |
| 3  | Hiking |
| 4  | Mountain Biking |
| 5  | Running |
| 6  | Walking |

**How imports are triggered**

The command scans once and exits — there is no built-in watch loop. Use one of:

- **One-shot (Docker):**
  ```bash
  # Uses default tcx_sport_mapping.json — no flags needed for TCX files
  docker compose exec fittrackee \
    ftcli workouts import_dir --dir /usr/src/app/import --on-success move
  ```

- **Cron** (runs every 15 minutes; `-T` disables TTY for non-interactive use):
  ```cron
  */15 * * * * docker compose -f /path/to/docker-compose.yml exec -T fittrackee \
    ftcli workouts import_dir --dir /usr/src/app/import --on-success move
  ```

- **Systemd path unit** — triggers immediately when a file is dropped into the
  folder, without polling. Ideal for desktop setups.

The `--on-success move` flag moves processed files to `import/done/` so repeated
runs never re-import the same file.

**Examples:**

```bash
# TCX directory — sport inferred automatically from default mapping file
ftcli workouts import_dir --dir /mnt/tcx-drop --on-success move

# Override one entry (e.g. map "Other" to Walking instead of Hiking)
ftcli workouts import_dir --dir /mnt/tcx-drop --sport-mapping "Other:Walking" --on-success move

# Non-TCX files (GPX/FIT/KML/KMZ) — sport-id required as fallback
ftcli workouts import_dir --dir /mnt/gpx-drop --sport-id 5 --on-success move

# Mixed directory: TCX uses default mapping, GPX/FIT fall back to --sport-id
ftcli workouts import_dir --dir /mnt/mixed-drop --sport-id 5 --on-success move

# Target a specific user and delete originals after import
ftcli workouts import_dir --dir /mnt/gpx-drop --sport-id 5 \
  --username alice --on-success delete
```


#### Docker: mount an import directory

Uncomment the import volume in `docker-compose.yml`:

```yaml
- ${HOST_IMPORT_DIR:-./data/import}:/usr/src/app/import:z
```

Set the host path in `.env.docker` (optional, defaults to `./data/import`):

```bash
export HOST_IMPORT_DIR=/path/to/your/gpx/drop-folder
```

Then run imports inside the container:

```bash
# TCX files: sport inferred from tcx_sport_mapping.json automatically
docker compose exec fittrackee \
  ftcli workouts import_dir --dir /usr/src/app/import --on-success move
```

### Security: APP_SECRET_KEY minimum length

The application validates `APP_SECRET_KEY` on startup against the 32-byte
minimum required by HS256 (RFC 7518 §3.2):

- In **production** the app refuses to start if the key is shorter than 32 bytes.
- In **development** a warning is logged.

Generate a suitable key with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Docker CI

A GitHub Actions workflow (`.github/workflows/docker.yml`) builds the image
and pushes it to the private registry at `repo.dev.posch.org` on every push to
`main`/`dev` and on `v*` tags. Requires a `REPO_PWD` secret in the repository
settings.

---

## Repositories

The main repository is hosted on [Codeberg.org](https://codeberg.org/FitTrackee/FitTrackee).  
The [Github repository](https://github.com/SamR1/FitTrackee) is a mirror (except for issues and PRs). For now, it is used to run tests, as well as to build and publish Python packages and Docker images using GitHub Actions (see [issue](https://codeberg.org/FitTrackee/FitTrackee/issues/1121)).

## Documentation

- [Features](https://docs.fittrackee.org/en/features/index.html)
- [Installation instructions](https://docs.fittrackee.org/en/installation/index.html)
- [Command line interface](https://docs.fittrackee.org/en/cli.html)
- [Third-party tools](https://docs.fittrackee.org/en/third_party_tools.html)
- [Changelog](https://docs.fittrackee.org/en/changelog.html)
- [Troubleshooting](https://docs.fittrackee.org/en/troubleshooting/index.html)
- [Contributing](https://docs.fittrackee.org/en/contributing.html)

**Under heavy development (some features may be unstable).**  
(see [provisional roadmap](https://codeberg.org/FitTrackee/FitTrackee/issues/1010), [issues](https://codeberg.org/FitTrackee/FitTrackee/issues) and [documentation](https://docs.fittrackee.org) for more information)  

![FitTrackee Dashboard Screenshot](https://docs.fittrackee.org/en/_images/dashboard.png)

## Translations

FitTrackee uses [Weblate](https://hosted.weblate.org/engage/fittrackee/) for translation management.

Status (on development branch, may differ from the released version):

[![Translation status](https://hosted.weblate.org/widget/fittrackee/multi-auto.svg)](https://hosted.weblate.org/engage/fittrackee/)

---

1: _test coverage: only for Python API and CLI_ 
