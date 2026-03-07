import sys
import os
import json
import pool
class Game:
    def __init__(self,all_girls,all_npcs):
        self.all_girls=all_girls
        self.all_npcs=all_npcs
        self.pool=[pool.all_girls,pool.all_npcs]
        self.begin_love=False
        self.current_girl=None
        self.screen_idx_common=0
        self.screen_idx_girls=0
    
    def start_new_game(self):
        print("欢迎来到恋爱养成游戏！")
        #清空所有女角色好感度
        for girl in self.all_girls:
            girl.affinity=0
        if self.current_girl!=None:
            self.current_girl=None
        self.begin_love=False
        self.screen_idx_common=0
        self.screen_idx_girls=0
        self.universal_story()
    
    def save_game(self):
        print("这里可以进行存档")
        choice=input("是否要进行存档（y/n）")
        if choice=='y':
            user_choice=input("请输入存档编号（1-5）")
            filename=os.path.join("save",f"save{user_choice}.json")
            with open(filename,'w',encoding="utf-8") as f:
                data={
                    "begin_love": self.begin_love,
                    "current_girl": self.current_girl.name if self.current_girl else None,
                    "screen_idx_common": self.screen_idx_common,
                    "screen_idx_girls": self.screen_idx_girls,
                    "affinity_data": {girl.name: girl.affinity for girl in self.all_girls}
                }
                json.dump(data,f)
        else:
            print("存档已取消。")
            return

    def load_game(self):
        print("这里可以进行读档")
        choice=input("是否要进行读档（y/n）")
        if choice=='y':
            user_choice=input("请输入存档编号（1-5）")
            filename=os.path.join("save",f"save{user_choice}.json")
            try:
                with open(filename,'r',encoding="utf-8") as f:
                    data=json.load(f)
                self.begin_love=data.get("begin_love",False)
                current_girl_name=data.get("current_girl")
                self.current_girl = next((girl for girl in self.all_girls if girl.name==current_girl_name),None)
                self.screen_idx_common=data.get("screen_idx_common",0)
                self.screen_idx_girls=data.get("screen_idx_girls",0)
                for name,affinity in data.get("affinity_data",{}).items():
                    girl=next((g for g in self.all_girls if g.name==name),None)
                    if girl:
                        girl.affinity=affinity
                
                if self.begin_love and self.current_girl:
                    print(f"欢迎回来！你正在和{self.current_girl.name}的个人线进行游戏。")
                    self.screen_idx_girls = self.current_girl.girl_story(self.screen_idx_girls)
                else:
                    print("欢迎回来！你正在通用故事线进行游戏。")
                    self.universal_story()
            except FileNotFoundError:
                print("存档文件不存在，请重新选择。")
                return
        else:
            print("读档已取消。")
            return
    def del_save(self):
        print("这里可以进行删除存档")
        choice=input("是否要删除存档（y/n）")
        if choice=='y':
            user_choice=input("请输入要删除的存档编号（1-5）")
            filename=os.path.join("save",f"save{user_choice}.json")
            if os.path.exists(filename):
                os.remove(filename)
                print(f"存档{user_choice}已删除。")
            else:
                print("存档文件不存在，请重新选择。")
                return
        else:
            print("删除存档已取消。")
            return
    def check_love(self) -> bool:
        for girl in self.all_girls:
            if girl.affinity>=100:
                self.begin_love=True
                self.current_girl=girl
                return True
        return False
    
    def universal_story(self):
        print("这里是通用故事线，可以在这里进行一些剧情发展和选择。")
        story_filename=os.path.join("story", "common.json")
        try:
            with open(story_filename,'r',encoding="utf-8") as f:
                story_data=json.load(f)
            steps=sorted(story_data.items(), key=lambda kv:int(kv[0].replace("step","")))
            if self.screen_idx_common >= len(steps):
                print("共通线结束")
                if self.check_love():
                    print(f"进入{self.current_girl.name}的个人线")
                    self.girl_unique_story()
                else:
                    print("很抱歉，你单身了")
                    self.start_game()
                    return
            for _,step_data in steps[self.screen_idx_common:]:
                print(f"[{step_data['speaker']}]: {step_data['text']}")
                if step_data.get("choice")=="True":
                    try:
                        choice=int(input())
                        if choice==1:
                            pass
                        if choice==2:
                            pass
                    except ValueError:
                        print("请输入有效的选项编号。")
                        return
                self.screen_idx_common+=1
        except FileNotFoundError:
            print("故事文件不存在。")
    def girl_unique_story(self):
        if self.begin_love == False or self.current_girl==None:
            print("你还没有进入女主角个人线")
            return
        print(f"这里是{self.current_girl.name}的个人故事线。")
        self.screen_idx_girls = self.current_girl.girl_story(self.screen_idx_girls)

    def start_game(self):
        while True:
            print("这是一个旮旯给木引擎")
            print("1.开始新游戏")
            print("2.读取存档")
            print("3.删除存档")
            print("4.退出游戏")
            choice=input("请输入选项编号：")
            if choice=='1':
                self.start_new_game()
            elif choice=='2':
                self.load_game()
            elif choice=='3':
                self.del_save()
            elif choice=='4':
                print("感谢游玩！")
                sys.exit()
            else:
                print("请输入有效的选项编号。")
    
    def run(self):
        self.start_game()

if __name__=="__main__":
    #这里需要根据pool.py中的角色池来初始化游戏
    game=Game(pool.all_girls,pool.all_npcs)
    game.run()