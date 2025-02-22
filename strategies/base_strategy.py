import abc

class BaseStrategy(abc.ABC):
    def __init__(self, df_data, config):
        self.data = df_data.copy()
        self.config = config

    @abc.abstractmethod
    def prepare_data(self):
        """Prepare the data (calculate indicators, etc.)"""
        pass

    @abc.abstractmethod
    def generate_signal(self):
        """Return a tuple (signal, timestamp) based on the strategy logic."""
        pass
