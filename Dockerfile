# Session Pilot Pro Plus — Dockerized Proof‑of‑Concept
# =====================================================
# This container bundles the skill, adapters, and a lightweight Python REPL so
# anyone can verify every command works without installing anything locally.

FROM python:3.11-slim

LABEL org.opencontainers.image.title="Session Pilot Pro Plus"
LABEL org.opencontainers.image.description="Token‑aware session memory & skill router – prompt‑only skill with real persistence"
LABEL org.opencontainers.image.version="1.4.0"
LABEL org.opencontainers.image.source="https://github.com/deprofessorie/session-pilot-pro-plus"

# ─── Install system deps (sqlite dev headers) ──────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        git gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# ─── Clone / copy skill (context is mounted at runtime; fall back to repo) ─
WORKDIR /opt/skill
COPY session-pilot-pro_SKILL.md /opt/skill/SKILL.md
COPY STORAGE_ADAPTERS.md /opt/skill/STORAGE_ADAPTERS.md
COPY EVALUATION.md /opt/skill/EVALUATION.md
COPY COMPATIBILITY.md /opt/skill/COMPATIBILITY.md
COPY README.md /opt/skill/README.md
COPY adapters/ /opt/skill/adapters/

# ─── Add the skill folder to the standard OpenCode location ────────────────
RUN mkdir -p /root/.config/opencode/skills/session-pilot-pro-plus
COPY session-pilot-pro_SKILL.md /root/.config/opencode/skills/session-pilot-pro-plus/SKILL.md
COPY adapters/ /root/.config/opencode/skills/session-pilot-pro-plus/adapters/

# ─── Set env defaults ─────────────────────────────────────────────────────
ENV SESSION_PILOT_HOME=/data/session-pilot
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ─── Expose optional REPL port (for remote demo) ─────────────────────────
EXPOSE 8765

# ─── Default command: drop into an interactive Python REPL wired to the skill
CMD ["python", "/opt/skill/scripts/repl.py"]
