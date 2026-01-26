"""
Flask API skeleton for Skill Scope.
"""

import json
import tempfile
from typing import Any, Dict

from flask import Flask, jsonify, request

from file_parser import check_file_validity
from services.scan_service import run_scan


def _parse_bool(value, default=False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return default


def _parse_advanced_options(value) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return {}


def _json_safe(payload: Any) -> Any:
    return json.loads(json.dumps(payload, default=str))


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/scans")
    def create_scan():
        payload = request.get_json(silent=True) or {}
        analysis_mode = (
            request.form.get("analysis_mode")
            or payload.get("analysis_mode")
            or "basic"
        )
        consent = _parse_bool(
            request.form.get("consent") or payload.get("consent"),
            default=False,
        )
        persist = _parse_bool(
            request.form.get("persist") or payload.get("persist"),
            default=True,
        )
        advanced_options = _parse_advanced_options(
            request.form.get("advanced_options") or payload.get("advanced_options")
        )

        zip_file = request.files.get("zip")
        zip_path = payload.get("zip_path")

        if zip_file:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
            zip_file.save(tmp.name)
            tmp.close()
            zip_path = tmp.name

        if not zip_path:
            return jsonify({"error": "zip file or zip_path is required"}), 400

        file_list = check_file_validity(zip_path)
        if not file_list:
            return jsonify({"error": "invalid or empty zip file"}), 400

        results = run_scan(
            file_list,
            analysis_mode,
            advanced_options,
            consent=consent,
            persist=persist,
        )

        return jsonify(
            {
                "analysis_mode": analysis_mode,
                "persisted": persist,
                "results": _json_safe(results),
            }
        )

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=True)
