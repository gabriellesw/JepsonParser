import yaml
import os


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            env = os.getenv("ENVIRONMENT")
            with open("config.yaml") as f:
                conf = yaml.safe_load(f)
            section = conf[env]
            instance = super(Config, cls).__new__(cls)
            for k, v in section.items():
                instance.__setattr__(k, v)
            cls._instance = instance
        return cls._instance

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return os.path.join(
            self.DB_URI_PREFIX,
            os.path.abspath(os.path.dirname(__file__)),
            self.DB_NAME
        )
