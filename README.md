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

This fork adds two quality-of-life features for self-hosted single-user deployments.

### Disable registration

Set the environment variable `REGISTRATION_DISABLED=true` to permanently close
new account sign-ups regardless of the `max_users` admin setting:

```bash
# .env
export REGISTRATION_DISABLED=true
```

The API returns `403 error, registration is disabled` for any registration
attempt, and the frontend correctly reports registration as unavailable.  
The existing `max_users` admin config field continues to work normally when the
variable is not set.

### Automated GPX / workout file import from a local directory

The `ftcli workouts import_dir` CLI command scans a local directory for workout
files and imports them for a given user and sport — useful for drop-folder
automation with cron or a systemd path unit.

**Supported formats:** GPX, FIT, TCX, KML, KMZ

```
Usage: ftcli workouts import_dir [OPTIONS]

  Import all workout files from a local directory.

  Supported formats: gpx, fit, tcx, kml, kmz.
  Files are processed in alphabetical order.

Options:
  --dir DIRECTORY          Directory containing workout files to import.
                           [required]
  --sport-id INTEGER       Sport id for imported workouts.  [required]
  --username TEXT          Username to import workouts for. Defaults to the
                           only active user when just one exists.
  --on-success [keep|move|delete]
                           Action after a successful import: 'keep' leaves the
                           file in place, 'move' moves it to a done/
                           subdirectory, 'delete' removes it.  [default: keep]
  -v, --verbose            Enable verbose output log.
```

**Examples:**

```bash
# Import all GPX files; keep originals in place (single-user: no --username needed)
ftcli workouts import_dir --dir /mnt/gpx-drop --sport-id 1

# Move each successfully imported file to /mnt/gpx-drop/done/
ftcli workouts import_dir --dir /mnt/gpx-drop --sport-id 1 --on-success move

# Delete originals after import, target a specific user
ftcli workouts import_dir --dir /mnt/gpx-drop --sport-id 2 \
  --username alice --on-success delete
```

**Cron example** (import every 15 minutes, move on success):

```cron
*/15 * * * * ftcli workouts import_dir --dir /mnt/gpx-drop --sport-id 1 --on-success move
```

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
