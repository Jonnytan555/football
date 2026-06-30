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
