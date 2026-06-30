-- Football Predictor — table definitions
-- Run with psql:  psql "$DATABASE_URL" -f scripts/create_tables.sql
-- Or via Python:  python scripts/create_tables.py
--
-- football_teams is created automatically by the ingestion handler
-- on the first run of:  python -m ingestion.main teams

-- --------------------------------------------------------
-- Match results and upcoming fixtures
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS football_matches (
    match_id         BIGINT,
    utc_date         TIMESTAMPTZ,
    status           TEXT,
    competition_id   INTEGER,
    competition_name TEXT,
    home_team_id     INTEGER,
    home_team        TEXT,
    away_team_id     INTEGER,
    away_team        TEXT,
    winner           TEXT,
    home_goals       INTEGER,
    away_goals       INTEGER,
    last_updated     TIMESTAMPTZ
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_football_matches_match_id'
    ) THEN
        ALTER TABLE football_matches
            ADD CONSTRAINT uq_football_matches_match_id UNIQUE (match_id);
    END IF;
END $$;

-- --------------------------------------------------------
-- League standings (season snapshot per team)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS football_standings (
    competition_id   INTEGER,
    competition_name TEXT,
    season           INTEGER,
    position         INTEGER,
    team_id          INTEGER,
    team_name        TEXT,
    played           INTEGER,
    won              INTEGER,
    draw             INTEGER,
    lost             INTEGER,
    points           INTEGER,
    goals_for        INTEGER,
    goals_against    INTEGER,
    goal_difference  INTEGER,
    form             TEXT
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_football_standings_competition_id_season_team_id'
    ) THEN
        ALTER TABLE football_standings
            ADD CONSTRAINT uq_football_standings_competition_id_season_team_id
            UNIQUE (competition_id, season, team_id);
    END IF;
END $$;

-- --------------------------------------------------------
-- Model predictions for upcoming fixtures
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS football_predictions (
    match_id          BIGINT,
    utc_date          TIMESTAMPTZ,
    competition       TEXT,
    home_team         TEXT,
    away_team         TEXT,
    prob_home_win     DOUBLE PRECISION,
    prob_draw         DOUBLE PRECISION,
    prob_away_win     DOUBLE PRECISION,
    predicted_outcome TEXT,
    predicted_on      DATE
);

-- --------------------------------------------------------
-- Rolling model accuracy log
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS football_prediction_accuracy (
    evaluated_on     DATE,
    outcome          TEXT,
    correct          INTEGER,
    total            INTEGER,
    accuracy         DOUBLE PRECISION,
    overall_accuracy DOUBLE PRECISION
);
