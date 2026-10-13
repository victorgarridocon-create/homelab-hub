from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from ..models import AppService, Hardware, Misc, VM
from ..utils import monitor

bp = Blueprint("status", __name__, url_prefix="/api/status")


def _targets():
    return monitor.build_targets(Hardware.query.all(), VM.query.all(), AppService.query.all(), Misc.query.all())


@bp.route("", methods=["GET"])
def get_status():
    """Reachability of every item with an address, keyed by "<type>-<id>".

    Answers immediately with the latest results; checks run in a background thread. "checking" is
    true while new results are on the way (the frontend then polls again shortly).
    """
    config = current_app.config
    force = request.args.get("refresh") in ("1", "true")
    targets = _targets()
    _, checked_at, cached_signature, running = monitor.snapshot()
    stale = force or cached_signature != monitor.signature(targets)

    if config.get("STATUS_SYNC"):
        # Tests: check inline so results are deterministic
        if stale:
            monitor.refresh(targets, config["STATUS_TIMEOUT_SECONDS"])
    else:
        monitor.ensure_background(current_app._get_current_object(), _targets, config["STATUS_INTERVAL_SECONDS"])
        # A run in progress already covers this request unless the user explicitly asked again
        if force or (stale and not running):
            monitor.request_refresh()

    results, checked_at, _, running_now = monitor.snapshot()
    # Items deleted since the last check disappear right away
    keys = {t["key"] for t in targets}
    results = {k: v for k, v in results.items() if k in keys}
    return jsonify(
        data=results,
        checked_at=datetime.fromtimestamp(checked_at, timezone.utc).isoformat() if checked_at else None,
        checking=bool(running_now or (stale and not config.get("STATUS_SYNC"))),
        # "stale" includes the first run, when there are no results yet
        up=sum(1 for r in results.values() if r["status"] == "up"),
        down=sum(1 for r in results.values() if r["status"] == "down"),
    )
