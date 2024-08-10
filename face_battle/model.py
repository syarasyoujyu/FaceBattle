from pydantic import BaseModel

class Player(BaseModel):
    user_name: str
    image_path: str
    point:int
    description:str

class Result(BaseModel):
    ranking: list[Player]
    comment: str

    def output(self,theme) -> str:
        return f"お題：{theme}\n"+"\n".join([f"\n{player.user_name}:{player.point}点" for player in self.ranking]) + f"\n{self.comment}"