from pydantic import BaseModel
from pathlib import Path


class Player(BaseModel):
    user_name: str
    image_path: Path

class Result(BaseModel):
    ranking: list[Player]
    comment: str