import pandas as pd


class BaselineModel:
    def __init__(self):
        """
        Initialize the model.

        Args:
            model_name: The name of the model.
            model_version: The version of the model.
        """
        pass

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Fit the model.

        Args:
            X_train: The training data.
            y_train: The training target.
        """
        pass

    def predict(self, X_test: pd.DataFrame) -> pd.Series:
        """
        Predict the target.

        Args:
            X_test: The test data.

        Returns:
            The predicted target.
        """
        return X_test['closing_price']
