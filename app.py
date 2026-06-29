from __future__ import annotations

import atexit

from flask import Flask, jsonify, render_template, request

from scheduler import SchedulerEngine


def create_app(testing: bool = False, engine: SchedulerEngine | None = None) -> Flask:
    app = Flask(__name__)
    scheduler_engine = engine or SchedulerEngine(autostart=not testing)
    app.config["ENGINE"] = scheduler_engine
    app.config["TESTING"] = testing

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok"}, 200

    @app.get("/api/state")
    def get_state():
        return jsonify(scheduler_engine.snapshot())

    @app.post("/api/jobs")
    def create_job():
        payload = request.get_json(silent=True) or request.form
        name = str(payload.get("name", "")).strip()
        burst_value = payload.get("burst_time", 0)
        try:
            burst_time = int(burst_value)
            job = scheduler_engine.add_job(name, burst_time)
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify({"job": job.to_dict(), "state": scheduler_engine.snapshot()}), 201

    @app.post("/api/reset")
    def reset():
        scheduler_engine.reset()
        return jsonify(scheduler_engine.snapshot())

    if not testing:
        atexit.register(scheduler_engine.stop)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
