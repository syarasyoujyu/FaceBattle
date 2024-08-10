import os
from model import Player, Result
import base64
from jinja2 import Template 
from loguru import logger
from litellm import completion
import os

def face_battle(theme: str, players: list[Player]) -> Result:
    try: 
        # プレイヤーを点数順に並び替える
        players.sort(key=lambda x: x.point,reverse=True)
        #優勝者を決める
        top_point=players[0].point
        top_players=[player for player in players if player.point==top_point]
        comment=make_comment(top_players,theme)
        return Result(ranking=players, comment=f"{comment}")
    except Exception as e:
        logger.warning(e)
        
    raise NotImplementedError("実装してね")

def send_request_to_gpt4o(messages:list)->str:
    """リクエストを送信し、レスポンスを取得する関数"""
    try:
        response = completion(
            model="gpt-4o",
            messages=messages,
            api_key=os.environ["OPENAI_API_KEY"],
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(e)
    return "エラーが発生しました。"

def praise_top_player(top_player:Player,theme:str)->str:
    """優勝者を褒めるコメントを作成する関数"""
    praise_template="""{{top_player_description}}から、{{top_player_name}}さんのどこが評価されたのかを述べて、ほめてください。なお、この大会は「{{theme}}の真似をする大会」で、コメントは一文でお願いします。
例1:SSAMMAさんは、怒りの表情がとてもよく表れているという点で、非常に優れています!
例2:UMMAさんは、マリオカートで勝った時特有の喜びがとてもよく表れていて、素晴らしいです!
"""
    top_player_name,top_player_description=top_player.user_name,top_player.description
    praise_content=Template(source=praise_template).render(top_player_name=top_player_name,top_player_description=top_player_description,theme=theme)
    messages=[
        {
            "role":"user",
            "content":praise_content
        }
    ]
    response=send_request_to_gpt4o(messages)
    return response
    

def make_comment(top_players:list,title:str)->str:
    """優勝者の名前を受け取り、コメントを作成する関数"""
    top_player_names=[player.user_name for player in top_players]
    praise_comments=[praise_top_player(player,title) for player in top_players]
    point=top_players[0].point
    comment="""優勝者は{{point}}点で、
{% for top_player_name  in top_player_names %}{{top_player_name}}さん{% if loop.index < top_player_names|length %},{% endif %}{% endfor %}
です！おめでとうございます！
{% for praise_comment in praise_comments %}
{{praise_comment}}
{% endfor %}
"""
    comment=Template(comment).render(point=point,top_player_names=top_player_names,praise_comments=praise_comments)
    return comment

