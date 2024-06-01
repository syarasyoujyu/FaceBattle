import os
from model import Player, Result

def face_battle(theme: str, players: list[Player]) -> Result:
    print(os.environ)
    if os.environ.get("IS_MOCK", "False") == "True":
        return Result(ranking=players[::-1], comment=f"これはモックの実装です。テーマ: {theme}")
    
    raise NotImplementedError("実装してね")