import pandas as pd
import sqlalchemy as sa
from shared.db import engine

FORM_WINDOW = 5


def load_matches() -> pd.DataFrame:
    query = """
        SELECT
            match_id, utc_date, competition_id, competition_name,
            home_team_id, home_team, away_team_id, away_team,
            home_goals, away_goals, winner, status
        FROM football_matches
        WHERE status = 'FINISHED'
          AND home_goals IS NOT NULL
          AND away_goals IS NOT NULL
        ORDER BY utc_date
    """
    with engine.connect() as conn:
        return pd.read_sql(sa.text(query), conn, parse_dates=["utc_date"])


def _team_results(matches: pd.DataFrame) -> pd.DataFrame:
    home = matches[["match_id", "utc_date", "home_team_id", "away_team_id", "home_goals", "away_goals", "winner"]].copy()
    home = home.rename(columns={"home_team_id": "team_id", "away_team_id": "opp_id", "home_goals": "gf", "away_goals": "ga"})
    home["venue"] = "home"
    home["result"] = home["winner"].map({"HOME_TEAM": "W", "DRAW": "D", "AWAY_TEAM": "L"})

    away = matches[["match_id", "utc_date", "home_team_id", "away_team_id", "home_goals", "away_goals", "winner"]].copy()
    away = away.rename(columns={"away_team_id": "team_id", "home_team_id": "opp_id", "away_goals": "gf", "home_goals": "ga"})
    away["venue"] = "away"
    away["result"] = away["winner"].map({"AWAY_TEAM": "W", "DRAW": "D", "HOME_TEAM": "L"})

    return pd.concat([home, away], ignore_index=True).sort_values("utc_date")


def _rolling_form(team_results: pd.DataFrame, window: int = FORM_WINDOW) -> pd.DataFrame:
    tr = team_results.copy()
    tr["win"] = (tr["result"] == "W").astype(int)
    tr["draw"] = (tr["result"] == "D").astype(int)
    tr["loss"] = (tr["result"] == "L").astype(int)
    tr["points"] = tr["win"] * 3 + tr["draw"]
    grp = tr.groupby("team_id", sort=False)
    for col in ["win", "draw", "loss", "gf", "ga", "points"]:
        tr[f"roll_{col}"] = grp[col].transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    return tr[["match_id", "team_id", "venue", "roll_win", "roll_draw", "roll_loss", "roll_gf", "roll_ga", "roll_points"]]


def _venue_split_form(team_results: pd.DataFrame, window: int = FORM_WINDOW) -> pd.DataFrame:
    tr = team_results.copy()
    tr["win"] = (tr["result"] == "W").astype(int)
    rows = []
    for venue in ("home", "away"):
        vtr = tr[tr["venue"] == venue].copy()
        grp = vtr.groupby("team_id", sort=False)
        for col in ["win", "gf", "ga"]:
            vtr[f"venue_roll_{col}"] = grp[col].transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
        rows.append(vtr[["match_id", "team_id", "venue", "venue_roll_win", "venue_roll_gf", "venue_roll_ga"]])
    return pd.concat(rows, ignore_index=True)


def _days_rest(team_results: pd.DataFrame) -> pd.DataFrame:
    tr = team_results[["match_id", "utc_date", "team_id", "venue"]].copy().sort_values("utc_date")
    tr["prev_date"] = tr.groupby("team_id")["utc_date"].shift(1)
    tr["days_rest"] = (tr["utc_date"] - tr["prev_date"]).dt.days
    return tr[["match_id", "team_id", "venue", "days_rest"]]


def _h2h(matches: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in matches.iterrows():
        past = matches[
            (matches["utc_date"] < row["utc_date"]) & (
                ((matches["home_team_id"] == row["home_team_id"]) & (matches["away_team_id"] == row["away_team_id"])) |
                ((matches["home_team_id"] == row["away_team_id"]) & (matches["away_team_id"] == row["home_team_id"]))
            )
        ].tail(10)
        if past.empty:
            rows.append({"match_id": row["match_id"], "h2h_home_win_rate": None, "h2h_meetings": 0})
            continue
        home_wins = (
            ((past["home_team_id"] == row["home_team_id"]) & (past["winner"] == "HOME_TEAM")) |
            ((past["away_team_id"] == row["home_team_id"]) & (past["winner"] == "AWAY_TEAM"))
        ).sum()
        rows.append({"match_id": row["match_id"], "h2h_home_win_rate": home_wins / len(past), "h2h_meetings": len(past)})
    return pd.DataFrame(rows)


def current_team_stats(matches: pd.DataFrame) -> dict[int, dict]:
    """Current rolling stats per team. Used at prediction time only — no shift()."""
    team_results = _team_results(matches)
    tr = team_results.copy()
    tr["win"] = (tr["result"] == "W").astype(int)
    tr["draw"] = (tr["result"] == "D").astype(int)
    tr["loss"] = (tr["result"] == "L").astype(int)
    tr["points"] = tr["win"] * 3 + tr["draw"]
    grp = tr.groupby("team_id", sort=False)
    for col in ["win", "draw", "loss", "gf", "ga", "points"]:
        tr[f"roll_{col}"] = grp[col].transform(lambda s: s.rolling(FORM_WINDOW, min_periods=1).mean())
    latest = tr.sort_values("utc_date").groupby("team_id").last()
    return latest[["roll_win", "roll_draw", "roll_loss", "roll_gf", "roll_ga", "roll_points"]].to_dict(orient="index")


def h2h_stats(home_id: int, away_id: int, matches: pd.DataFrame) -> dict:
    h2h = matches[
        ((matches["home_team_id"] == home_id) & (matches["away_team_id"] == away_id)) |
        ((matches["home_team_id"] == away_id) & (matches["away_team_id"] == home_id))
    ].tail(10)
    if h2h.empty:
        return {"h2h_home_win_rate": 0.0, "h2h_meetings": 0}
    home_wins = (
        ((h2h["home_team_id"] == home_id) & (h2h["winner"] == "HOME_TEAM")) |
        ((h2h["away_team_id"] == home_id) & (h2h["winner"] == "AWAY_TEAM"))
    ).sum()
    return {"h2h_home_win_rate": round(home_wins / len(h2h), 3), "h2h_meetings": len(h2h)}


def build_features() -> pd.DataFrame:
    """Training-ready DataFrame. One row per finished match, no future leakage."""
    matches = load_matches()
    team_results = _team_results(matches)
    rolling = _rolling_form(team_results)
    venue_form = _venue_split_form(team_results)
    rest = _days_rest(team_results)
    h2h = _h2h(matches)

    def team_features(df_feat: pd.DataFrame, venue: str, prefix: str) -> pd.DataFrame:
        subset = df_feat[df_feat["venue"] == venue].drop(columns="venue")
        return subset.add_prefix(prefix).rename(columns={f"{prefix}match_id": "match_id", f"{prefix}team_id": f"{prefix}team_id"})

    df = (
        matches
        .merge(team_features(rolling, "home", "home_"), on="match_id", how="left")
        .merge(team_features(rolling, "away", "away_"), on="match_id", how="left")
        .merge(team_features(venue_form, "home", "home_"), on="match_id", how="left")
        .merge(team_features(venue_form, "away", "away_"), on="match_id", how="left")
        .merge(team_features(rest, "home", "home_"), on="match_id", how="left")
        .merge(team_features(rest, "away", "away_"), on="match_id", how="left")
        .merge(h2h, on="match_id", how="left")
    )

    df["target"] = df["winner"].map({"HOME_TEAM": 0, "DRAW": 1, "AWAY_TEAM": 2})

    feature_cols = [
        "match_id", "utc_date", "competition_id", "home_team_id", "away_team_id",
        "home_roll_win", "home_roll_draw", "home_roll_loss", "home_roll_gf", "home_roll_ga", "home_roll_points",
        "away_roll_win", "away_roll_draw", "away_roll_loss", "away_roll_gf", "away_roll_ga", "away_roll_points",
        "home_venue_roll_win", "home_venue_roll_gf", "home_venue_roll_ga",
        "away_venue_roll_win", "away_venue_roll_gf", "away_venue_roll_ga",
        "home_days_rest", "away_days_rest",
        "h2h_home_win_rate", "h2h_meetings",
        "target",
    ]

    return df[feature_cols].dropna(subset=["target"])
