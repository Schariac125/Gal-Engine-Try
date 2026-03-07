import os
import json

class Character:
    def __init__(self,name,role):
        self.name=name
        self.role=role

class MainCharacter(Character):
    def __init__(self,name,role="MainGirl",affinity=0):
        super().__init__(name,role)
        self.affinity=affinity
    
    def change_affinity(self,change_amount):
        self.affinity+=change_amount
        print(f"{self.name}的好感度上升了{change_amount}点，目前好感度为{self.affinity}点。")

    def get_affinity(self):
        return self.affinity
    
    def is_love(self) -> bool:
        if self.affinity >= 100:
            return True
        else:
            return False
    #这个地方留给子类实现不同角色的个人线剧情
    def girl_story(self,screen_idx,game=None):
        pass

    def girl_end(self):
        print(f"{self.name}的个人线已经结束了！")

#这只是一个示例角色，后续可以根据需要添加更多角色
class Shori(MainCharacter):
    def __init__(self,name="Shori"):
        super().__init__(name)

    def girl_story(self,screen_idx,game=None):
        idx=screen_idx
        story_filename=os.path.join("story","girls",f"{self.name}.json")
        try:
            with open(story_filename,'r',encoding="utf-8") as f:
                story_data=json.load(f)
                steps=sorted(story_data.items(), key=lambda kv:int(kv[0].replace("step","")))
                if idx>=len(steps):
                    print("剧情已经结束了")
                    return screen_idx
                else:
                    for _,story_text in steps[idx:]:
                        print(f"{story_text['speaker']}:{story_text['text']}")
                        screen_idx+=1
                        if game is not None:
                            command_result=game.prompt_story_command()
                            if command_result=="menu":
                                game.open_story_menu()
                                return screen_idx
                    return screen_idx
        except FileNotFoundError:
            print("剧情文件不存在。")
            return screen_idx
    
    def girl_end(self):
        print(f"{self.name}的个人线已经结束了！")