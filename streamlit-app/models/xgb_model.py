# instance of xgb model (pycaret) or other source


from models.base_model import BaseModel

class XGBModel(BaseModel):
    def __init__(self):
       pass

    def load(self):
        pass

# TODO this method is invalid, it does not prepare input expected from fcnn model
    def prepare_input(self):
        pass

    def predict(self):
       pass