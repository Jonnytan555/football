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
