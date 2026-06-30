# Football DB Schema — R Reference

Connect via RODBC or DBI:
```r
library(DBI)
library(odbc)

con <- dbConnect(odbc(),
  Driver   = "ODBC Driver 17 for SQL Server",
  Server   = "localhost",
  Database = "FOOTYHUB",
  Trusted_Connection = "Yes"
)
```

---

## dbo.FootballDataOrg — Match results

| Column | Type | Notes |
|---|---|---|
| match_id | int | Primary key |
| utc_date | datetime | Kick-off time UTC |
| status | varchar | FINISHED / SCHEDULED / POSTPONED |
| competition_id | int | See competition IDs below |
| competition_name | varchar | e.g. "Premier League" |
| home_team_id | int | FK to FootballTeams |
| home_team | varchar | |
| away_team_id | int | FK to FootballTeams |
| away_team | varchar | |
| winner | varchar | HOME_TEAM / DRAW / AWAY_TEAM / null |
| home_goals | int | null if not finished |
| away_goals | int | null if not finished |
| last_updated | datetime | |

Competition IDs: `2021` = Premier League, `2016` = Championship, `2001` = Champions League

---

## dbo.FootballStandings — Season standings

| Column | Type | Notes |
|---|---|---|
| competition_id | int | |
| competition_name | varchar | |
| season | int | Start year, e.g. 2023 = 2023/24 |
| position | int | League position at snapshot |
| team_id | int | FK to FootballTeams |
| team_name | varchar | |
| played | int | |
| won | int | |
| draw | int | |
| lost | int | |
| points | int | |
| goals_for | int | |
| goals_against | int | |
| goal_difference | int | |
| form | varchar | e.g. "W,D,W,L,W" (last 5) |

---

## dbo.FootballTeams — Team reference

| Column | Type | Notes |
|---|---|---|
| id | int | Primary key |
| name | varchar | |
| shortName | varchar | |
| tla | varchar | Three-letter abbreviation |
| crest | varchar | URL |
| website | varchar | |
| founded | int | |
| venue | varchar | Stadium name |

---

## dbo.FootballPredictions — Python model output

| Column | Type | Notes |
|---|---|---|
| match_id | int | FK to FootballDataOrg |
| utc_date | datetime | |
| competition | varchar | |
| home_team | varchar | |
| away_team | varchar | |
| prob_home_win | float | Model probability 0–1 |
| prob_draw | float | |
| prob_away_win | float | |
| predicted_outcome | varchar | Home Win / Draw / Away Win |
| predicted_on | date | When prediction was made |

---

## dbo.FootballPredictionAccuracy — Model tracking

| Column | Type | Notes |
|---|---|---|
| evaluated_on | date | |
| outcome | varchar | Home Win / Draw / Away Win |
| correct | int | Count correct |
| total | int | Count total |
| accuracy | float | |
| overall_accuracy | float | Across all outcomes |

---

## Useful queries

```r
# All finished Premier League matches
matches <- dbGetQuery(con, "
  SELECT * FROM dbo.FootballDataOrg
  WHERE competition_id = 2021
    AND status = 'FINISHED'
  ORDER BY utc_date
")

# Current season standings
standings <- dbGetQuery(con, "
  SELECT * FROM dbo.FootballStandings
  WHERE season = 2024
  ORDER BY competition_id, position
")

# Compare Python predictions vs actuals
comparison <- dbGetQuery(con, "
  SELECT p.home_team, p.away_team, p.predicted_outcome,
         p.prob_home_win, p.prob_draw, p.prob_away_win,
         m.winner AS actual_winner, m.home_goals, m.away_goals
  FROM dbo.FootballPredictions p
  JOIN dbo.FootballDataOrg m ON p.match_id = m.match_id
  WHERE m.status = 'FINISHED'
")
```
