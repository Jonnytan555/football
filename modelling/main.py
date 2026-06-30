"""
Modelling entry point. Run from the football/ root directory.

    python -m modelling.main train
    python -m modelling.main train --compare
    python -m modelling.main predict
    python -m modelling.main predict --retrain
    python -m modelling.main accuracy
"""
import logging
import sys
import traceback

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "predict"
    try:
        if mode == "train":
            from modelling.python.features import build_features
            from modelling.python.predictor import FootballPredictor, compare_models
            df = build_features()
            print(f"Dataset: {len(df)} matches")
            if "--compare" in sys.argv:
                compare_models(df)
            else:
                p = FootballPredictor()
                stats = p.train(df)
                p.save()
                print(f"Accuracy: {stats['accuracy']:.1%}  (train={stats['train_rows']}, test={stats['test_rows']})")

        elif mode == "predict":
            from modelling.python.predict_upcoming import run
            run(retrain="--retrain" in sys.argv)

        elif mode == "accuracy":
            from modelling.python.accuracy_tracker import evaluate
            evaluate()

        else:
            print(f"Unknown mode '{mode}'. Use: train | predict | accuracy")
            sys.exit(1)

    except Exception:
        logging.error(traceback.format_exc())
