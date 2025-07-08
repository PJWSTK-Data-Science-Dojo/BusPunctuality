from abc import ABC, abstractmethod

class BaseModel(ABC):
    @abstractmethod
    def load(self): pass

    @abstractmethod
    def prepare_input(self, *args, **kwargs): pass

    @abstractmethod
    def predict(self, features): pass
