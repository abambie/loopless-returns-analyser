from __future__ import annotations  # enables modern type-hint syntax on Python 3.9
from dataclasses import dataclass, field  # dataclass: auto-generates __init__; field: lets us set mutable defaults safely
from typing import Any, Dict, List, Tuple  # type hint aliases used in method signatures
import numpy as np  # NumPy: used to convert the model's prediction array to a plain Python list
import pandas as pd  # pandas: all training and scoring data is passed as DataFrames

from sklearn.compose import ColumnTransformer  # applies different transformations to categorical vs numeric columns
from sklearn.preprocessing import OneHotEncoder  # converts categorical string columns (e.g. "category") into binary indicator columns
from sklearn.pipeline import Pipeline  # (imported for potential future use; the current implementation uses ColumnTransformer directly)
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score  # evaluation metrics used after training to report model performance
from sklearn.model_selection import train_test_split  # splits data into training and test sets for unbiased evaluation
from sklearn.linear_model import LogisticRegression  # the classifier used: simple, fast, and explainable via its coefficients
import joblib  # serialises and deserialises the trained model object to/from disk

from .repository import DataRepository, FilterMap  # DataRepository: configurable local/remote data-access layer; FilterMap: type alias for filter dicts


@dataclass  # auto-generates __init__ so FeatureEngineer(categorical_columns=..., numeric_columns=...) works without boilerplate
class FeatureEngineer:  # transforms raw DataFrame columns into a numeric feature matrix suitable for scikit-learn
    categorical_columns: List[str]  # names of the columns that contain string categories (e.g. ["category", "brand", "season", "size", "color"])
    numeric_columns: List[str]  # names of the columns that contain numeric values passed straight through (e.g. ["original_price", "markdown_percentage", "customer_rating"])
    fitted: bool = False  # flag: True after fit() has been called; prevents transform() being called before the encoder has learned the category levels
    feature_names: List[str] = field(default_factory=list)  # list of final feature names (set after fitting); used by the feature importance chart in app.py
    transformer: Any = None  # the fitted ColumnTransformer object; None until fit() is called

    def fit(self, df: pd.DataFrame) -> None:  # learns the category levels from the training data and builds the ColumnTransformer
        X = df[self.categorical_columns + self.numeric_columns].copy()  # select only the feature columns (no target) from the training DataFrame

        self.transformer = ColumnTransformer(  # combine a OneHotEncoder for categoricals and a passthrough for numerics into one transformer
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), self.categorical_columns),  # "cat": one-hot encodes categorical columns; handle_unknown="ignore" prevents errors on unseen categories at score time
                ("num", "passthrough", self.numeric_columns),  # "num": passes numeric columns through unchanged (no scaling or encoding)
            ],
            remainder="drop",  # drop any columns not listed in categorical_columns or numeric_columns
        )
        self.transformer.fit(X)  # fit the ColumnTransformer to the training data — this is where the encoder learns which categories exist
        self.fitted = True  # mark as fitted so transform() is allowed to run

        # Feature names (best effort)
        try:  # wrapped in try/except because get_feature_names_out() may not be available on older scikit-learn versions
            ohe = self.transformer.named_transformers_["cat"]  # retrieve the fitted OneHotEncoder from the ColumnTransformer
            cat_names = list(ohe.get_feature_names_out(self.categorical_columns))  # get the full list of one-hot column names (e.g. "category_Dresses", "brand_Zara")
        except Exception:  # if the method is unavailable (older sklearn) or fails for any reason
            cat_names = []  # fall back to an empty list — the feature chart will just show blank names
        self.feature_names = cat_names + self.numeric_columns  # final feature name list = one-hot names + raw numeric column names

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:  # applies the fitted ColumnTransformer to a DataFrame and returns a dense numeric DataFrame
        self._ensure_fitted()  # guard: raise an error if fit() hasn't been called yet
        X = df[self.categorical_columns + self.numeric_columns].copy()  # select only the required columns
        X_t = self.transformer.transform(X)  # apply the fitted encoder and passthrough — result is a sparse or dense matrix
        # Convert to dense DataFrame for downstream convenience
        X_dense = X_t.toarray() if hasattr(X_t, "toarray") else X_t  # convert sparse matrix to dense array if needed (OneHotEncoder returns sparse by default)
        return pd.DataFrame(X_dense, columns=self.feature_names)  # wrap the dense array in a DataFrame with proper column names

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:  # convenience method: calls fit() then transform() in one step
        self.fit(df)  # fit the transformer on this DataFrame
        return self.transform(df)  # immediately transform the same DataFrame and return it

    def get_feature_names(self) -> List[str]:  # returns the list of feature names set during fit() — used by app.py to label the feature importance chart
        return self.feature_names  # return the stored list of feature name strings

    def _ensure_fitted(self) -> None:  # internal guard: raises a clear error if transform() is called before fit()
        if not self.fitted or self.transformer is None:  # check both the flag and the actual transformer object
            raise RuntimeError("FeatureEngineer is not fitted. Call fit() first.")  # descriptive error so the developer knows what went wrong


@dataclass  # auto-generates __init__ so RiskPredictionModel() works without boilerplate
class RiskPredictionModel:  # wraps a scikit-learn LogisticRegression and adds save/load and prediction helpers
    model_type: str = "logistic_regression"  # identifier for the model type (kept for documentation; the model is always LogisticRegression in this version)
    model_object: Any = None  # the actual scikit-learn model instance; created in __post_init__ if not provided
    is_trained: bool = False  # flag: True after train() or load() has been called

    def __post_init__(self) -> None:  # runs automatically after __init__; creates the LogisticRegression if no model was injected
        if self.model_object is None:  # only create a default model if one wasn't explicitly passed in
            # Simple, explainable baseline classifier
            self.model_object = LogisticRegression(max_iter=1000, class_weight="balanced")  # class_weight="balanced" stops the model ignoring rare returns by weighting each class inversely to its frequency

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:  # fits the LogisticRegression on the transformed feature matrix X and target labels y
        self.model_object.fit(X, y)  # scikit-learn fit: learns the weights (coefficients) that best predict is_returned from the features
        self.is_trained = True  # mark as trained so predict() is allowed to run

    def predict(self, X: pd.DataFrame) -> List[int]:  # returns binary predictions (0 or 1) for each row in X
        self._ensure_trained()  # guard: raise a clear error if the model hasn't been trained yet
        return self.model_object.predict(X).tolist()  # scikit-learn predict returns a NumPy array; tolist() converts to a plain Python list

    def predict_proba(self, X: pd.DataFrame) -> List[float]:  # returns the predicted probability of return (class 1) for each row in X
        self._ensure_trained()  # guard: raise a clear error if the model hasn't been trained yet
        proba = self.model_object.predict_proba(X)[:, 1]  # predict_proba returns shape (n_rows, 2): column 0 = prob of not returned, column 1 = prob of returned
        return proba.tolist()  # convert NumPy array to a plain Python list of floats

    def save(self, path: str) -> None:  # serialises the trained model object to disk using joblib so it can be reloaded in a future session
        joblib.dump(self.model_object, path)  # joblib.dump is more efficient than pickle for large NumPy arrays inside scikit-learn models

    def load(self, path: str) -> None:  # deserialises a previously saved model from disk and marks it as trained
        self.model_object = joblib.load(path)  # read the model back from the joblib file
        self.is_trained = True  # mark as trained because a loaded model is ready to predict

    def _ensure_trained(self) -> None:  # internal guard: raises a clear error if predict is called before training
        if not self.is_trained:  # check the flag
            raise RuntimeError("Model not trained. Call train() or load() first.")  # descriptive error so the developer knows what went wrong


@dataclass  # auto-generates __init__ so RiskPredictionService(repository=..., feature_engineer=..., model=...) works without boilerplate
class RiskPredictionService:  # orchestrates the full ML pipeline: fetch data → encode features → train/score → return risk-ranked products
    repository: DataRepository  # injected data-access layer — fetches purchase records from the configured backend
    feature_engineer: FeatureEngineer  # injected feature engineer — transforms raw columns into numeric features
    model: RiskPredictionModel  # injected model wrapper — trains LogisticRegression and generates risk probabilities
    risk_threshold: float = 0.5  # probability threshold above which a prediction is labelled as "high risk" (default: 50%)

    def train_model(self, filters: FilterMap = None) -> Dict[str, Any]:
        # Load and clean the dataset for training
        if filters is None:
            filters = {}
        df = self.repository.load_dataset(filters)
        df = self._prepare_training_df(df)
        if df.empty:
            raise ValueError("No training data after filtering/cleaning.")

        # Split features/target, then 80/20 stratified train-test split
        X, y = self._split_features_target(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # Fit the feature encoder on the training set only, then transform both splits
        self.feature_engineer.fit(X_train)
        X_train_t = self.feature_engineer.transform(X_train)
        X_test_t = self.feature_engineer.transform(X_test)

        # Fit the logistic regression on the encoded training data
        self.model.train(X_train_t, y_train)

        # Evaluate on the held-out test set
        y_pred  = np.array(self.model.predict(X_test_t))
        y_proba = np.array(self.model.predict_proba(X_test_t))  # probability of class 1 (returned), used for threshold-independent metrics
        # ROC AUC measures discrimination across all thresholds. Falls back to 0 if y_test contains only one class.
        try:
            roc_auc = float(roc_auc_score(y_test, y_proba))
        except ValueError:
            roc_auc = 0.0
        metrics = {
            "accuracy":         float(accuracy_score(y_test, y_pred)),
            "precision":        float(precision_score(y_test, y_pred, zero_division=0)),
            "recall":           float(recall_score(y_test, y_pred, zero_division=0)),
            "f1":               float(f1_score(y_test, y_pred, zero_division=0)),
            "roc_auc":          roc_auc,
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "feature_count":    len(self.feature_engineer.get_feature_names()),
        }
        return metrics

    def score_risk(self, filters: FilterMap = None) -> pd.DataFrame:
        # Load the same columns the model was trained on
        if filters is None:
            filters = {}
        df = self.repository.load_dataset(filters)
        if df.empty:
            return df
        X = df[self.feature_engineer.categorical_columns + self.feature_engineer.numeric_columns].copy()

        # Impute missing values so the encoder does not fail
        for col in self.feature_engineer.categorical_columns:
            if col in X.columns:
                X[col] = X[col].fillna("Unknown")
        for col in self.feature_engineer.numeric_columns:
            if col in X.columns:
                X[col] = X[col].fillna(X[col].median())

        # Generate return probabilities and threshold them into a binary flag
        X_t = self.feature_engineer.transform(X)
        df = df.copy()
        df["risk_score"] = self.model.predict_proba(X_t)
        df["predicted_return"] = (df["risk_score"] >= self.risk_threshold).astype(int)
        return df

    def get_high_risk_products(self, top_n: int, filters: FilterMap = None) -> List[Dict[str, Any]]:
        # Score every purchase row
        if filters is None:
            filters = {}
        scored = self.score_risk(filters)
        if scored.empty:
            return []

        # Aggregate to product level, sort descending, keep top N
        grp = scored.groupby("product_id")["risk_score"].mean().reset_index()
        grp.rename(columns={"risk_score": "avg_risk_score"}, inplace=True)
        grp = grp.sort_values("avg_risk_score", ascending=False).head(int(top_n))
        return grp.to_dict(orient="records")

    def explain_record(self, record: Dict[str, Any]) -> Dict[str, Any]:  # returns a lightweight explanation showing which feature values were used for a prediction (not SHAP — just the input values)
        """
        Lightweight explanation (not SHAP): return the feature values used.
        """
        keys = self.feature_engineer.categorical_columns + self.feature_engineer.numeric_columns  # the list of feature column names the model uses
        used = {k: record.get(k) for k in keys}  # extract the feature values from the record dict (None if a key is missing)
        return {"used_features": used, "note": "Explanation shows feature values used by the model input."}  # return the feature dict with a clarifying note

    def set_risk_threshold(self, t: float) -> None:  # updates the probability threshold used to classify predictions as high-risk
        self.risk_threshold = float(t)  # cast to float for safety; any row with risk_score >= t will be labelled predicted_return = 1

    def _prepare_training_df(self, df: pd.DataFrame) -> pd.DataFrame:  # cleans the raw DataFrame to ensure it's valid for training
        if df.empty:  # nothing to prepare
            return df  # return the empty DataFrame immediately
        # Ensure label exists and valid
        if "is_returned" not in df.columns:  # the target column must exist
            return pd.DataFrame()  # return an empty DataFrame if the target is missing — training cannot proceed
        df = df.dropna(subset=["is_returned"])  # drop rows where the target label is missing (NaN) — they can't be used for supervised learning
        df["is_returned"] = df["is_returned"].astype(int).clip(0, 1)  # cast to int and clip to {0, 1} to ensure clean binary labels
        # Drop rows missing required feature fields
        needed = self.feature_engineer.categorical_columns + self.feature_engineer.numeric_columns  # all columns that must be present for training
        for c in needed:  # check each required column
            if c not in df.columns:  # if the column is completely absent from the dataset
                return pd.DataFrame()  # return empty — can't train without this feature
        df = df.dropna(subset=needed)  # drop any remaining rows that have NaN in any required feature column
        return df  # return the cleaned DataFrame ready for feature engineering and training

    def _split_features_target(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:  # separates the feature matrix X from the target Series y
        X = df[self.feature_engineer.categorical_columns + self.feature_engineer.numeric_columns].copy()  # select only the feature columns (no target, no ID columns)
        y = df["is_returned"].astype(int)  # the target: 1 = returned, 0 = not returned; cast to int for compatibility with scikit-learn
        return X, y  # return the feature matrix and target as a tuple
