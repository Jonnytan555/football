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
