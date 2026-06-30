CREATE TABLE IF NOT EXISTS football_prediction_accuracy (
    evaluated_on     DATE,
    outcome          TEXT,
    correct          INTEGER,
    total            INTEGER,
    accuracy         DOUBLE PRECISION,
    overall_accuracy DOUBLE PRECISION
);
