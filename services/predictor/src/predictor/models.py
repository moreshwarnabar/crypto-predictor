from typing import Optional, Type, Union

import numpy as np
import optuna
import pandas as pd
from loguru import logger
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class HuberRegressorWithHyperParameterTuning:
    def __init__(self, hyper_params: dict):
        """
        Initialize the model.

        Args:
            hyper_params: The hyper-parameters for the model.
        """
        self.hyper_params = hyper_params
        self.pipe = self._create_pipe()

    def _create_pipe(self, params: Optional[dict] = None):
        if params is None:
            params = {}
        return Pipeline(
            [
                ('scaler', StandardScaler()),
                ('model', HuberRegressor(**params)),
            ]
        )

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Fit the model.

        Args:
            X_train: The training data.
            y_train: The training target.
        """
        if self.hyper_params.get('hyper_param_trials', 0) == 0:
            logger.info(
                'No hyper-parameter tuning. Fitting the model with the default parameters'
            )
        else:
            # perform the hyper-parameter search
            logger.info('Performing hyper-parameter tuning')
            best_params = self._hyper_parameter_search(
                X_train,
                y_train,
                self.hyper_params['hyper_param_trials'],
                self.hyper_params['hyper_param_folds'],
            )
            logger.info(f'Best hyper-parameters: {best_params}')

            logger.info('Fitting the model with the best hyper-parameters')
            self.pipe = self._create_pipe(best_params)

        self.pipe.fit(X_train, y_train)

    def predict(self, X_test: pd.DataFrame) -> pd.Series:
        """
        Predict the target.

        Args:
            X_test: The test data.

        Returns:
            The predicted target.
        """
        return self.pipe.predict(X_test)

    def _hyper_parameter_search(
        self, X_train: pd.DataFrame, y_train: pd.Series, num_trials: int, num_folds: int
    ):
        """
        Perform hyper-parameter tuning with Optuna.

        Args:
            X_train: The training data.
            y_train: The training target.
            num_trials: The number of trials to run.
            num_folds: The number of folds to use for cross-validation.

        Returns:
            The best model.
        """

        # define the objective function to be minimized for the HuberRegressor
        def objective(trial: optuna.Trial):
            """
            Define the objective function to be minimized for the HuberRegressor.

            Args:
                trial: The trial object.

            Returns:
                The mean absolute error of the model.
            """
            # define the hyperparameters to be tuned
            params = {
                'epsilon': trial.suggest_float('epsilon', 1, 9999999999),
                'alpha': trial.suggest_float('alpha', 0, 9999999999),
                'max_iter': trial.suggest_int('max_iter', 100, 1000),
                'tol': trial.suggest_float('tol', 1e-4, 1e-1),
                'fit_intercept': trial.suggest_categorical(
                    'fit_intercept', [True, False]
                ),
            }

            # use time-series split cross-validation to ensure the time-series order is preserved for each fold
            tscv = TimeSeriesSplit(n_splits=num_folds)
            mae_scores = []
            for train_idx, val_idx in tscv.split(X_train):
                X_train_fold, X_val_fold = (
                    X_train.iloc[train_idx],
                    X_train.iloc[val_idx],
                )
                y_train_fold, y_val_fold = (
                    y_train.iloc[train_idx],
                    y_train.iloc[val_idx],
                )

                # train the model
                pipe = self._create_pipe(params)
                pipe.fit(X_train_fold, y_train_fold)

                # evaluate the model
                y_pred = pipe.predict(X_val_fold)
                mae_scores.append(mean_absolute_error(y_val_fold, y_pred))

            return np.mean(mae_scores)

        # perform the hyper-parameter search
        logger.info(
            f'Performing hyper-parameter search with {num_trials} trials and {num_folds} folds'
        )
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=num_trials)

        # return the best model
        return study.best_trial.params


Model = Union[Type[HuberRegressorWithHyperParameterTuning]]


def get_model(model_name: str) -> Model:
    """
    Factory function to get a model.

    Args:
        model_name: The name of the model.

    Returns:
        The model.
    """
    if model_name == 'HuberRegressor':
        logger.info('Getting HuberRegressorWithHyperParameterTuning model')
        return HuberRegressorWithHyperParameterTuning(
            hyper_params={
                'hyper_param_trials': 0,
                'hyper_param_folds': 3,
            }
        )
    else:
        raise ValueError(f'Model {model_name} not found')


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
