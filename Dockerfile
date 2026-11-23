# Session Pilot Pro Plus — Dockerized Proof‑of‑Concept
# =====================================================
# This container bundles the skill, adapters, and a lightweight Python REPL so
# anyone can verify every command works without installing anything locally.

FROM python:3.11-slim

LABEL org.opencontainers.image.title="Session Pilot Pro Plus"
LABEL org.opencontainers.image.description="Unified agent memory, skill routing, and execution control platform"
LABEL org.opencontainers.image.version="2.1.0"
LABEL org.opencontainers.image.source="https://github.com/deprofessorie/session-pilot-pro-plus"

# ─── Install system deps (sqlite dev headers) ──────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        git gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# ─── Clone / copy skill (context is mounted at runtime; fall back to repo) ─
WORKDIR /opt/skill
COPY SKILL.md /opt/skill/SKILL.md
COPY session-pilot-pro_SKILL.md /opt/skill/session-pilot-pro_SKILL.md
COPY STORAGE_ADAPTERS.md /opt/skill/STORAGE_ADAPTERS.md
COPY EVALUATION.md /opt/skill/EVALUATION.md
COPY COMPATIBILITY.md /opt/skill/COMPATIBILITY.md
COPY BENCHMARKS.md /opt/skill/BENCHMARKS.md
COPY README.md /opt/skill/README.md
COPY adapters/ /opt/skill/adapters/
COPY references/ /opt/skill/references/
COPY scripts/ /opt/skill/scripts/

# ─── Add the skill folder to the standard OpenCode location ────────────────
RUN mkdir -p /root/.config/opencode/skills/session-pilot-pro-plus
COPY SKILL.md /root/.config/opencode/skills/session-pilot-pro-plus/SKILL.md
COPY adapters/ /root/.config/opencode/skills/session-pilot-pro-plus/adapters/
COPY references/ /root/.config/opencode/skills/session-pilot-pro-plus/references/
COPY scripts/ /root/.config/opencode/skills/session-pilot-pro-plus/scripts/

# ─── Set env defaults ─────────────────────────────────────────────────────
ENV SESSION_PILOT_HOME=/data/session-pilot
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ─── Expose optional REPL port (for remote demo) ─────────────────────────
EXPOSE 8765

# ─── Default command: drop into an interactive Python REPL wired to the skill
CMD ["python", "/opt/skill/scripts/repl.py"]
