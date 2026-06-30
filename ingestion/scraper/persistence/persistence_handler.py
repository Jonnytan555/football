from abc import ABC, abstractmethod
import pandas as pd


class PersistenceHandler(ABC):

    @abstractmethod
    def handle(self, new_df: pd.DataFrame, dropNa: bool = False, dtypes=None, created_date: str = 'CreatedDate'):
        pass
