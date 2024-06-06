from pydantic import BaseModel
from pathlib import Path


class Player(BaseModel):
    user_name: str
    image_path: Path

class Result(BaseModel):
    ranking: list[Player]
    comment: str

    def output(self) -> str:
        return "\n".join([f"{player.user_name}" for player in self.ranking]) + f"\n{self.comment}"