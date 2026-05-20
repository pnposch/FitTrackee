import logging
import os
import sys
from datetime import datetime
from logging import Logger
from typing import Optional

import click

from fittrackee.cli.app import app
from fittrackee.users.models import User
from fittrackee.workouts.constants import WORKOUT_ALLOWED_EXTENSIONS
from fittrackee.workouts.models import Sport
from fittrackee.workouts.services.workouts_from_file_refresh_service import (
    WorkoutsFromFileRefreshService,
)
from fittrackee.workouts.services.workouts_without_file_refresh_service import (  # noqa
    WorkoutsWithoutFileRefreshService,
)
from fittrackee.workouts.tasks import (
    process_workouts_archive_upload,
    process_workouts_archives_uploads,
)
from fittrackee.workouts.utils.workouts import get_workout_datetime

WORKOUT_VALID_EXTENSIONS = ", ".join(WORKOUT_ALLOWED_EXTENSIONS)
VALID_ON_ERROR_CHOICES = ["remove-references", "delete-workout"]

logger = logging.getLogger("fittrackee_workouts_cli")
logger.setLevel(logging.INFO)


def validate_order(
    ctx: click.core.Context, param: click.core.Option, value: Optional[str]
) -> Optional[str]:
    if value and value not in ["asc", "desc"]:
        raise click.BadParameter("order must be 'asc' or 'desc'")
    return value


def validate_extension(
    ctx: click.core.Context, param: click.core.Option, value: Optional[str]
) -> Optional[str]:
    if value and value not in WORKOUT_ALLOWED_EXTENSIONS:
        raise click.BadParameter(
            f"valid extensions are: {WORKOUT_VALID_EXTENSIONS}"
        )
    return value


def validate_sport_id(
    ctx: click.core.Context, param: click.core.Option, value: Optional[int]
) -> Optional[int]:
    with app.app_context():
        if value is not None and not Sport.query.filter_by(id=value).first():
            raise click.BadParameter(f"invalid sport id '{value}'")
    return value


def validate_user(
    ctx: click.core.Context, param: click.core.Option, value: Optional[str]
) -> Optional[str]:
    with app.app_context():
        if (
            value is not None
            and not User.query.filter_by(username=value).first()
        ):
            raise click.BadParameter(f"user '{value}' does not exist")
    return value


def validate_number(
    ctx: click.core.Context, param: click.core.Option, value: Optional[int]
) -> Optional[int]:
    if value is not None and value < 1:
        raise click.BadParameter("value must be greater than 0")

    return value


def validate_date(
    ctx: click.core.Context, param: click.core.Option, value: Optional[str]
) -> Optional["datetime"]:
    if value is not None:
        try:
            date_value, _ = get_workout_datetime(
                workout_date=value,
                user_timezone=None,
                date_str_format="%Y-%m-%d",
            )
            return date_value
        except Exception as e:
            raise click.BadParameter(
                f"'{value}' does not match format '%Y-%m-%d'"
            ) from e
    return value


def validate_on_file_error(
    ctx: click.core.Context, param: click.core.Option, value: Optional[str]
) -> Optional[str]:
    if value and value not in VALID_ON_ERROR_CHOICES:
        raise click.BadParameter(
            f"valid choices are: {', '.join(VALID_ON_ERROR_CHOICES)}"
        )
    return value


@click.group(name="workouts")
def workouts_cli() -> None:
    """Manage workouts."""
    pass


@workouts_cli.command("archive_uploads")
@click.option(
    "--max",
    "max_archives",
    type=int,
    required=True,
    help="Maximum number of workouts archive to process.",
)
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output log (default: disabled).",
)
def workouts_archive_uploads(max_archives: int, verbose: bool) -> None:
    """
    Process workouts archive uploads if queued tasks exist (progress = 0 and
    not aborted/errored).
    To use in case redis is not set.
    """
    with app.app_context():
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        count = process_workouts_archives_uploads(max_archives, logger)
        logger.info(f"\nWorkouts archives processed: {count}.")


@workouts_cli.command("archive_upload")
@click.option(
    "--id",
    "task_short_id",
    type=str,
    required=True,
    help="Id of task to process",
)
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output log (default: disabled).",
)
def process_queued_archive_upload(task_short_id: str, verbose: bool) -> None:
    """
    Process given queued workouts archive upload.

    To use in case redis is not set.
    """
    with app.app_context():
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        try:
            process_workouts_archive_upload(task_short_id, logger)
        except Exception as e:
            logger.error(str(e))
            sys.exit(1)
        logger.info("\nDone.")


def refresh_workouts_with_file(
    logger_: "Logger",
    sport_id: Optional[int] = None,
    new_sport_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    per_page: int = 10,
    page: int = 1,
    order: str = "asc",
    user: Optional[str] = None,
    extension: Optional[str] = None,
    with_weather: bool = False,
    with_elevation: bool = False,
    on_file_error: Optional[str] = None,
    verbose: bool = False,
) -> None:
    if with_elevation:
        if (
            app.config["OPEN_ELEVATION_API_URL"]
            or app.config["VALHALLA_API_URL"]
        ):
            click.secho(
                "\nWarning: Open Elevation and/or Valhalla API "
                "are set.\n"
                "If users have enabled missing elevation processing, "
                "multiple calls will be made to the elevation services "
                "depending on the number of workouts to be refreshed, "
                "which may result in rate limit errors.\n"
                "Adjust the number of workouts to refresh with "
                "'--per-page' option if necessary "
                f"(current value: {per_page}).",
                fg="yellow",
                bold=True,
            )
            if not click.confirm("Do you want to continue?"):
                click.echo("Aborted!")
                sys.exit(0)
        else:
            click.secho(
                "\nWarning: '--with-elevation' is provided but "
                "no elevation API URL is set.\n",
                fg="yellow",
            )
    try:
        service = WorkoutsFromFileRefreshService(
            sport_id=sport_id,
            new_sport_id=new_sport_id,
            date_from=date_from,
            date_to=date_to,
            per_page=per_page,
            page=page,
            order=order,
            user=user,
            extension=extension,
            with_weather=with_weather,
            verbose=verbose,
            with_elevation=with_elevation,
            on_file_error=on_file_error,
            logger=logger_,
        )
        service.refresh()
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


def refresh_workouts_without_file(
    logger_: "Logger",
    sport_id: Optional[int] = None,
    new_sport_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    per_page: int = 10,
    page: int = 1,
    order: str = "asc",
    user: Optional[str] = None,
    verbose: bool = False,
) -> None:
    try:
        service = WorkoutsWithoutFileRefreshService(
            logger=logger_,
            sport_id=sport_id,
            new_sport_id=new_sport_id,
            date_from=date_from,
            date_to=date_to,
            per_page=per_page,
            page=page,
            order=order,
            user=user,
            verbose=verbose,
        )
        service.refresh()
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


@workouts_cli.command("refresh")
@click.option(
    "--sport-id",
    help="sport id",
    type=int,
    callback=validate_sport_id,
)
@click.option(
    "--new-sport-id",
    help=(
        "sport id to which the workouts will be associated "
        "(must be provided with '--sport-id')"
    ),
    type=int,
    callback=validate_sport_id,
)
@click.option(
    "--from",
    "date_from",
    help="start date (format: %Y-%m-%d)",
    callback=validate_date,
)
@click.option(
    "--to",
    "date_to",
    help="end date (format: %Y-%m-%d)",
    callback=validate_date,
)
@click.option(
    "--per-page",
    help="number of workouts per page (default: 10)",
    type=int,
    callback=validate_number,
    default=10,
)
@click.option(
    "--page",
    help="page number (default: 1)",
    type=int,
    callback=validate_number,
    default=1,
)
@click.option(
    "--order",
    help="workout date order: 'asc' or 'desc' (default: 'asc')",
    type=str,
    default="asc",
    callback=validate_order,
)
@click.option(
    "--user",
    help="username of workouts owner",
    type=str,
    callback=validate_user,
)
@click.option(
    "--extension",
    help=(
        "workout file extension "
        f"(valid values are: {WORKOUT_VALID_EXTENSIONS})"
    ),
    type=str,
    callback=validate_extension,
)
@click.option(
    "--with-weather",
    help=(
        "enable weather data collection if weather provider is set and "
        "workout has no weather data. "
        "WARNING: depending on subscription, the rate limit can be reached, "
        "leading to errors and preventing weather data being collected during "
        "next uploads until the limit is reset (default: disabled)"
    ),
    is_flag=True,
    show_default=True,
    default=False,
)
@click.option(
    "--with-elevation",
    help=(
        "enable elevation update when elevation provider is set and "
        "some elevation data are missing. "
        "If disabled, existing elevation are not removed when elevation data "
        "are missing in the original file. "
        "WARNING: depending on subscription, the rate limit can be reached, "
        "leading to errors and preventing elevation data being collected "
        "during next uploads until the limit is reset (default: disabled)"
    ),
    is_flag=True,
    show_default=True,
    default=False,
)
@click.option(
    "--on-file-error",
    help=(
        "action to perform when workout file is not found. If not provided, "
        "an error will be raised. Valid actions are: 'remove-references' ("
        "all files references will be removed and workout preserved but not "
        "updated since no file found) and 'delete-workout'."
    ),
    type=str,
    callback=validate_on_file_error,
)
@click.option(
    "--without-file",
    help=(
        "allow to refresh workouts without a file and created before v1.1.0 "
        "to recalculate pace values (by default refresh command only "
        "refreshes workouts created with a file). "
        "When provided only workouts without file and without paces are "
        "refreshed (in this case '--extension', '--with-weather', "
        "'--with-elevation' and '--on-file-error' options are ignored). "
        "When not provided, only workouts with file are refreshed "
        "(default: disabled)"
    ),
    is_flag=True,
    show_default=True,
    default=False,
)
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    help="enable verbose output log (default: disabled)",
)
def refresh_workouts(
    sport_id: Optional[int] = None,
    new_sport_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    per_page: int = 10,
    page: int = 1,
    order: str = "asc",
    user: Optional[str] = None,
    extension: Optional[str] = None,
    with_weather: bool = False,
    with_elevation: bool = False,
    on_file_error: Optional[str] = None,
    without_file: bool = False,
    verbose: bool = False,
) -> None:
    """
    Refresh workouts
    """
    with app.app_context():
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        if new_sport_id and not sport_id:
            raise click.BadOptionUsage(
                "--new-sport-id",
                "'--new-sport-id' must be provided with '--sport-id'",
            )

        if without_file:
            if (
                extension is not None
                or with_weather
                or with_elevation
                or on_file_error
            ):
                click.secho(
                    "\nWarning: when '--without-file' is provided, following "
                    "options are ignored: '--extension', '--with-weather', "
                    "'--with-elevation' and '--on-file-error'.\n",
                    fg="yellow",
                )

            refresh_workouts_without_file(
                logger_=logger,
                sport_id=sport_id,
                new_sport_id=new_sport_id,
                date_from=date_from,
                date_to=date_to,
                per_page=per_page,
                page=page,
                order=order,
                user=user,
                verbose=verbose,
            )
        else:
            refresh_workouts_with_file(
                logger_=logger,
                sport_id=sport_id,
                new_sport_id=new_sport_id,
                date_from=date_from,
                date_to=date_to,
                per_page=per_page,
                page=page,
                order=order,
                user=user,
                extension=extension,
                with_weather=with_weather,
                verbose=verbose,
                with_elevation=with_elevation,
                on_file_error=on_file_error,
            )

        logger.info("\nDone.")


@workouts_cli.command("import_dir")
@click.option(
    "--dir",
    "import_dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, readable=True
    ),
    required=True,
    help="Directory containing workout files to import.",
)
@click.option(
    "--username",
    help=(
        "Username to import workouts for. "
        "Defaults to the only active user when just one exists."
    ),
    type=str,
    callback=validate_user,
)
@click.option(
    "--sport-id",
    help="Sport id for imported workouts.",
    type=int,
    required=True,
    callback=validate_sport_id,
)
@click.option(
    "--on-success",
    "on_success",
    type=click.Choice(["keep", "move", "delete"]),
    default="keep",
    show_default=True,
    help=(
        "Action after a file is successfully imported: "
        "'keep' leaves it in place, "
        "'move' moves it to a 'done/' subdirectory, "
        "'delete' removes it."
    ),
)
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output log (default: disabled).",
)
def import_dir(
    import_dir: str,
    username: Optional[str],
    sport_id: int,
    on_success: str,
    verbose: bool,
) -> None:
    """
    Import all workout files from a local directory.

    Supported formats: gpx, fit, tcx, kml, kmz.
    Files are processed in alphabetical order.
    """
    from werkzeug.datastructures import FileStorage

    from fittrackee import db
    from fittrackee.workouts.exceptions import (
        WorkoutException,
        WorkoutFileException,
    )
    from fittrackee.workouts.services.workouts_from_file_creation_service import (  # noqa
        WorkoutsFromFileCreationService,
    )

    with app.app_context():
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        if username:
            user: Optional[User] = User.query.filter_by(
                username=username
            ).first()
        else:
            active_users = User.query.filter_by(is_active=True).all()
            if len(active_users) == 0:
                logger.error("No active users found.")
                sys.exit(1)
            if len(active_users) > 1:
                logger.error(
                    "Multiple users exist; use --username to select one."
                )
                sys.exit(1)
            user = active_users[0]

        if user is None:
            logger.error("User not found.")
            sys.exit(1)

        files = sorted(
            entry
            for entry in os.listdir(import_dir)
            if os.path.isfile(os.path.join(import_dir, entry))
            and entry.rsplit(".", 1)[-1].lower() in WORKOUT_ALLOWED_EXTENSIONS
        )

        if not files:
            logger.info("No workout files found in directory.")
            return

        done_dir = os.path.join(import_dir, "done")
        if on_success == "move":
            os.makedirs(done_dir, exist_ok=True)

        imported = 0
        errored = 0
        for filename in files:
            filepath = os.path.join(import_dir, filename)
            logger.info(f"Importing {filename}...")
            try:
                with open(filepath, "rb") as f:
                    file_storage = FileStorage(stream=f, filename=filename)
                    service = WorkoutsFromFileCreationService(
                        auth_user=user,
                        workouts_data={"sport_id": sport_id},
                        file=file_storage,
                    )
                    service.process()
                imported += 1
                if verbose:
                    logger.debug("  > imported.")
                if on_success == "delete":
                    os.remove(filepath)
                elif on_success == "move":
                    os.rename(filepath, os.path.join(done_dir, filename))
            except (WorkoutException, WorkoutFileException) as e:
                errored += 1
                db.session.rollback()
                error_msg = (
                    e.args[1] if len(e.args) > 1 else str(e)  # type: ignore
                )
                logger.error(f"  > error: {error_msg}")
            except Exception as e:
                errored += 1
                db.session.rollback()
                logger.error(f"  > unexpected error: {e}")

        logger.info(f"\nDone. Imported: {imported}, errored: {errored}.")
