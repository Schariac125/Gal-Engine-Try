import sys
import os
import json
import pool
import character


class Game:
    def __init__(self,all_girls):
        self.all_girls=all_girls
        self.begin_love=False
        self.current_girl=None
        self.screen_idx_common=0
        self.screen_idx_girls=0
        self.pending_choice_common=False

    def open_story_menu(self):
        print("已返回主菜单。")
        self.start_game()
    
    def start_new_game(self):
        print("欢迎来到恋爱养成游戏！")
        #清空所有女角色好感度
        for girl in self.all_girls.values():
            girl.affinity=0
        if self.current_girl!=None:
            self.current_girl=None
        self.begin_love=False
        self.screen_idx_common=0
        self.screen_idx_girls=0
        self.pending_choice_common=False
        self.universal_story()
    
    def save_game(self, need_confirm=True):
        if need_confirm:
            print("这里可以进行存档")
            choice=input("是否要进行存档（y/n）").strip().lower()
            if choice!='y':
                print("存档已取消。")
                return False

        while True:
            user_choice=input("请输入存档编号（1-5）").strip()
            if user_choice in {"1","2","3","4","5"}:
                break
            print("请输入有效的存档编号。")

        os.makedirs("save",exist_ok=True)
        filename=os.path.join("save",f"save{user_choice}.json")
        with open(filename,'w',encoding="utf-8") as f:
            data={
                "begin_love": self.begin_love,
                "current_girl": self.current_girl.name if self.current_girl else None,
                "screen_idx_common": self.screen_idx_common,
                "screen_idx_girls": self.screen_idx_girls,
                "pending_choice_common": self.pending_choice_common,
                "affinity_data": {girl.name: girl.affinity for girl in self.all_girls.values()}
            }
            json.dump(data,f,ensure_ascii=False,indent=2)
        print(f"存档{user_choice}保存成功。")
        return True

    def prompt_story_command(self, prompt_text="按回车继续，输入save存档，输入q返回主菜单："):
        while True:
            command=input(prompt_text).strip().lower()
            if command=="":
                return "continue"
            if command in {"save","s"}:
                self.save_game(need_confirm=False)
                continue
            if command in {"q","quit","menu"}:
                return "menu"
            print("请输入回车继续，输入save存档，或输入q返回主菜单。")

    def handle_choice_step(self, step_data):
        girl_name = step_data.get("girl")
        target_girl = self.all_girls.get(girl_name)
        if target_girl is None:
            print("当前剧情缺少对应的角色配置。")
            return "error"

        self.pending_choice_common=True
        command_result=self.prompt_story_command("按回车显示选项，输入save存档，输入q返回主菜单：")
        if command_result=="menu":
            return "menu"
        while True:
            choice = input("请输入选项编号（1/2，输入save可存档）：").strip().lower()
            if choice in {"save","s"}:
                self.save_game(need_confirm=False)
                continue
            if choice in {"q","quit","menu"}:
                self.pending_choice_common=False
                return "menu"
            if choice == '1':
                target_girl.change_affinity(10)
                self.pending_choice_common=False
                return "completed"
            if choice == '2':
                target_girl.change_affinity(-10)
                self.pending_choice_common=False
                return "completed"
            print("请输入有效的选项编号，或输入save存档、q返回主菜单。")

    def finish_common_story(self):
        print("共通线结束")
        if self.check_love():
            print(f"进入{self.current_girl.name}的个人线")
            self.girl_unique_story()
        else:
            print("很抱歉，你单身了")
            self.start_game()

    def load_game(self):
        print("这里可以进行读档")
        choice=input("是否要进行读档（y/n）").strip().lower()
        if choice=='y':
            user_choice=input("请输入存档编号（1-5）").strip()
            filename=os.path.join("save",f"save{user_choice}.json")
            try:
                with open(filename,'r',encoding="utf-8") as f:
                    data=json.load(f)
                self.begin_love=data.get("begin_love",False)
                current_girl_name=data.get("current_girl")
                self.current_girl = self.all_girls.get(current_girl_name)
                self.screen_idx_common=data.get("screen_idx_common",0)
                self.screen_idx_girls=data.get("screen_idx_girls",0)
                self.pending_choice_common=data.get("pending_choice_common",False)
                for name,affinity in data.get("affinity_data",{}).items():
                    girl=self.all_girls.get(name)
                    if girl:
                        girl.affinity=affinity
                
                if self.begin_love and self.current_girl:
                    print(f"欢迎回来！你正在和{self.current_girl.name}的个人线进行游戏。")
                    self.screen_idx_girls = self.current_girl.girl_story(self.screen_idx_girls,self)
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
        for girl in self.all_girls.values():
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
                self.finish_common_story()
                return
            while self.screen_idx_common < len(steps):
                _,step_data = steps[self.screen_idx_common]
                print(f"[{step_data['speaker']}]: {step_data['text']}")
                if step_data.get("choice") == "True":
                    choice_result=self.handle_choice_step(step_data)
                    if choice_result=="error":
                        return
                    if choice_result=="menu":
                        self.open_story_menu()
                        return
                    self.screen_idx_common+=1
                    continue
                self.screen_idx_common+=1
                command_result=self.prompt_story_command()
                if command_result=="menu":
                    self.open_story_menu()
                    return
            self.finish_common_story()
        except FileNotFoundError:
            print("故事文件不存在。")

    def girl_unique_story(self):
        if self.begin_love == False or self.current_girl==None:
            print("你还没有进入女主角个人线")
            return
        print(f"这里是{self.current_girl.name}的个人故事线。")
        self.screen_idx_girls = self.current_girl.girl_story(self.screen_idx_girls,self)

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
    game=Game(pool.all_girls)
    game.run()