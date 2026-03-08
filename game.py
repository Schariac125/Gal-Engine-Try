import sys
import os
import json
import check
import pool
import character


class Game:
    # 游戏初始化
    all_girls: dict

    def __init__(self, all_girls):
        self.all_girls = all_girls
        self.begin_love = False
        self.current_girl = None
        self.screen_idx_common = 0
        self.screen_idx_girls = 0
        self.pending_choice_common = False
        self.auto_skip_enabled = False

    def load_overall_history(self):
        os.makedirs("save", exist_ok=True)
        overall_filename = os.path.join("save", "save_overall.json")
        default_history = {"common": 0}
        for girl_name in self.all_girls:
            default_history[girl_name] = 0

        try:
            with open(overall_filename, "r", encoding="utf-8") as f:
                overall_data = json.load(f)
        except FileNotFoundError:
            overall_data = default_history
            with open(overall_filename, "w", encoding="utf-8") as f:
                json.dump(overall_data, f, ensure_ascii=False, indent=2)
            return overall_data

        updated = False
        for key, value in default_history.items():
            if key not in overall_data or not isinstance(overall_data.get(key), int):
                overall_data[key] = value
                updated = True
        if updated:
            with open(overall_filename, "w", encoding="utf-8") as f:
                json.dump(overall_data, f, ensure_ascii=False, indent=2)
        return overall_data

    def get_history_limit(self):
        overall_data = self.load_overall_history()
        if self.begin_love and self.current_girl is not None:
            return max(0, overall_data.get(self.current_girl.name, 0))
        return max(0, overall_data.get("common", 0))

    def open_story_menu(self):
        self.auto_skip_enabled = False
        print("已返回主菜单。")
        self.start_game()

    def start_new_game(self):
        print("欢迎来到恋爱养成游戏！")
        # 清空所有女角色好感度
        # 重置所有状态以保证新游戏不会与旧存档产生冲突
        for girl in self.all_girls.values():
            girl.affinity = 0
        if self.current_girl != None:
            self.current_girl = None
        self.begin_love = False
        self.screen_idx_common = 0
        self.screen_idx_girls = 0
        self.pending_choice_common = False
        self.auto_skip_enabled = False
        self.universal_story()

    # 实现记录历史最远点功能，为后续跳过历史已读剧情基础
    def save_overall(self):
        overall_filename = os.path.join("save", "save_overall.json")
        overall_data = self.load_overall_history()
        if not self.begin_love:
            history_common_idx = overall_data.get("common", 0)
            if self.screen_idx_common > history_common_idx:
                overall_data["common"] = self.screen_idx_common
                with open(overall_filename, "w", encoding="utf-8") as f:
                    json.dump(overall_data, f, ensure_ascii=False, indent=2)
            return

        if self.current_girl is None:
            return

        history_girl_idx = overall_data.get(self.current_girl.name, 0)
        if self.screen_idx_girls > history_girl_idx:
            overall_data[self.current_girl.name] = self.screen_idx_girls
            with open(overall_filename, "w", encoding="utf-8") as f:
                json.dump(overall_data, f, ensure_ascii=False, indent=2)

    def skip(self, steps, current_idx, history_limit, stop_at_choice=False):
        next_idx = current_idx
        while next_idx < len(steps):
            _, step_data = steps[next_idx]
            if stop_at_choice and step_data.get("choice") == "True":
                return next_idx
            if next_idx >= history_limit:
                return next_idx
            next_idx += 1
        return next_idx

    def execute_skip(self, steps, current_idx, history_limit, stop_at_choice=False):
        skip_target = self.skip(steps, current_idx, history_limit, stop_at_choice)
        if skip_target > current_idx:
            print(f"已跳过 {skip_target - current_idx} 条剧情。")
            return skip_target
        if self.auto_skip_enabled:
            self.auto_skip_enabled = False
            print("自动连续跳过已停止，前方没有可跳过的已读剧情。")
        return current_idx

    def save_game(self, need_confirm=True):
        if need_confirm:
            print("这里可以进行存档")
            choice = input("是否要进行存档（y/n）").strip().lower()
            if choice != "y":
                print("存档已取消。")
                return False

        while True:
            user_choice = input("请输入存档编号（1-5）").strip()
            if user_choice in {"1", "2", "3", "4", "5"}:
                break
            print("请输入有效的存档编号。")
        # 如果当前文件夹下不存在名为"save"的子文件夹，那么就创建一个
        os.makedirs("save", exist_ok=True)
        # 使用os.path.join获取子文件夹下的存档json文件真实路径
        filename = os.path.join("save", f"save{user_choice}.json")
        # encoding="utf-8"保证了中文也可以被正确解析
        try:
            with open(filename, "w", encoding="utf-8") as f:
                data = {
                    "begin_love": self.begin_love,
                    "current_girl": self.current_girl.name if self.current_girl else None,
                    "screen_idx_common": self.screen_idx_common,
                    "screen_idx_girls": self.screen_idx_girls,
                    "pending_choice_common": self.pending_choice_common,
                    "affinity_data": {
                        girl.name: girl.affinity for girl in self.all_girls.values()
                    },
                }
                # ensure_ascii也是用来保证中文被正确解析的
                json.dump(data, f, ensure_ascii=False, indent=2)
        finally:
            self.save_overall()
        print(f"存档{user_choice}保存成功。")
        return True

    # 这个交互逻辑用户获取用户的键盘反馈，将用户反馈暂存，实现真实旮旯给木效果
    def prompt_story_command(
        self,
        prompt_text="按回车继续，输入save存档，输入skip跳过已读，输入auto自动连续跳过，输入q返回主菜单：",
        allow_skip=True,
        allow_auto_skip=True,
    ):
        while True:
            # 去除空格并对大小写不敏感，一律转化为小写处理
            command = input(prompt_text).strip().lower()
            if command == "":
                return "continue"
            if command in {"save", "s"}:
                self.save_game(need_confirm=False)
                continue
            if allow_skip and command in {"skip", "sk"}:
                return "skip"
            if allow_auto_skip and command in {"auto", "a"}:
                self.auto_skip_enabled = True
                return "skip"
            if command in {"q", "quit", "menu"}:
                return "menu"
            if allow_skip and allow_auto_skip:
                print("请输入回车继续，输入save存档，输入skip跳过已读，输入auto自动连续跳过，或输入q返回主菜单。")
            elif allow_skip:
                print("请输入回车继续，输入save存档，输入skip跳过已读，或输入q返回主菜单。")
            else:
                print("请输入回车继续，输入save存档，或输入q返回主菜单。")

    # 单独实现选项的逻辑，这个需要等待后续优化
    # 已加入优化计划
    def handle_choice_step(self, step_data):
        girl_name = step_data.get("girl")
        target_girl = self.all_girls.get(girl_name)
        if target_girl is None:
            print("当前剧情缺少对应的角色配置。")
            return "error"

        self.pending_choice_common = True
        command_result = self.prompt_story_command(
            "按回车显示选项，输入save存档，输入q返回主菜单：",
            allow_skip=False,
            allow_auto_skip=False,
        )
        if command_result == "menu":
            return "menu"
        while True:
            choice = input("请输入选项编号（1/2，输入save可存档）：").strip().lower()
            if choice in {"save", "s"}:
                self.save_game(need_confirm=False)
                continue
            if choice in {"q", "quit", "menu"}:
                self.pending_choice_common = False
                return "menu"
            if choice == "1":
                target_girl.change_affinity(10)
                self.pending_choice_common = False
                return "completed"
            if choice == "2":
                target_girl.change_affinity(-10)
                self.pending_choice_common = False
                return "completed"
            print("请输入有效的选项编号，或输入save存档、q返回主菜单。")

    # 在共通线结尾进行判定，如果没有一个女角色的好感度达到既定值就输出单身回到主菜单
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
        choice = input("是否要进行读档（y/n）").strip().lower()
        if choice == "y":
            user_choice = input("请输入存档编号（1-5）").strip()
            filename = os.path.join("save", f"save{user_choice}.json")
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.begin_love = data.get("begin_love", False)
                current_girl_name = data.get("current_girl")
                self.current_girl = self.all_girls.get(current_girl_name)
                self.screen_idx_common = data.get("screen_idx_common", 0)
                self.screen_idx_girls = data.get("screen_idx_girls", 0)
                self.pending_choice_common = data.get("pending_choice_common", False)
                for name, affinity in data.get("affinity_data", {}).items():
                    girl = self.all_girls.get(name)
                    if girl:
                        girl.affinity = affinity
                # 这个逻辑用于判定是否进线，如果进线了就调用角色方法类里面的个人线开始游戏
                if self.begin_love and self.current_girl:
                    print(
                        f"欢迎回来！你正在和{self.current_girl.name}的个人线进行游戏。"
                    )
                    self.screen_idx_girls = self.current_girl.girl_story(
                        self.screen_idx_girls, self
                    )
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
        choice = input("是否要删除存档（y/n）")
        if choice == "y":
            user_choice = input("请输入要删除的存档编号（1-5）")
            filename = os.path.join("save", f"save{user_choice}.json")
            if os.path.exists(filename):
                os.remove(filename)
                print(f"存档{user_choice}已删除。")
            else:
                print("存档文件不存在，请重新选择。")
                return
        else:
            print("删除存档已取消。")
            return

    # 字典，只需要获取值就可以了
    def check_love(self) -> bool:
        for girl in self.all_girls.values():
            if girl.affinity >= 100:
                self.begin_love = True
                self.current_girl = girl
                return True
        return False

    def universal_story(self):
        print("这里是通用故事线，可以在这里进行一些剧情发展和选择。")
        story_filename = os.path.join("story", "common.json")
        try:
            with open(story_filename, "r", encoding="utf-8") as f:
                story_data = json.load(f)
            # 一个用来排序的lambda函数
            steps = sorted(
                story_data.items(), key=lambda kv: int(kv[0].replace("step", ""))
            )
            if self.screen_idx_common >= len(steps):
                self.finish_common_story()
                return
            history_limit = self.get_history_limit()
            while self.screen_idx_common < len(steps):
                _, step_data = steps[self.screen_idx_common]
                print(f"[{step_data['speaker']}]: {step_data['text']}")
                # 如果存档在json文件中读取到了choice被命令为真，那么会触发选项逻辑
                # 优化点：我觉得这里可以代码复用
                if step_data.get("choice") == "True":
                    choice_result = self.handle_choice_step(step_data)
                    if choice_result == "error":
                        return
                    if choice_result == "menu":
                        self.open_story_menu()
                        return
                    self.screen_idx_common += 1
                    self.save_overall()
                    history_limit = self.get_history_limit()
                    continue
                # 每一幕开始前就记得去把剧情的step加一，这样子才能实现正确的存档
                self.screen_idx_common += 1
                self.save_overall()
                history_limit = self.get_history_limit()
                if self.auto_skip_enabled:
                    self.screen_idx_common = self.execute_skip(
                        steps,
                        self.screen_idx_common,
                        history_limit,
                        stop_at_choice=True,
                    )
                    continue
                command_result = self.prompt_story_command()
                if command_result == "menu":
                    self.open_story_menu()
                    return
                if command_result == "skip":
                    self.screen_idx_common = self.execute_skip(
                        steps,
                        self.screen_idx_common,
                        history_limit,
                        stop_at_choice=True,
                    )
            self.finish_common_story()
        except FileNotFoundError:
            print("故事文件不存在。")

    # 函数开始时就检测是否是误触或者是通过修改json文件以达到条件，因为判定的两个函数只会在共通线结束被调用
    # 但直接改另一个信息我目前也没招
    # 优化点+1
    def girl_unique_story(self):
        if self.begin_love == False or self.current_girl == None:
            print("你还没有进入女主角个人线")
            return
        print(f"这里是{self.current_girl.name}的个人故事线。")
        self.screen_idx_girls = self.current_girl.girl_story(
            self.screen_idx_girls, self
        )

    def start_game(self):
        while True:
            print("这是一个旮旯给木引擎")
            print("1.开始新游戏")
            print("2.读取存档")
            print("3.删除存档")
            print("4.退出游戏")
            choice = input("请输入选项编号：")
            if choice == "1":
                self.start_new_game()
            elif choice == "2":
                self.load_game()
            elif choice == "3":
                self.del_save()
            elif choice == "4":
                print("感谢游玩！")
                sys.exit()
            else:
                print("请输入有效的选项编号。")

    def run(self):
        self.start_game()


if __name__ == "__main__":
    # 这里需要根据pool.py中的角色池来初始化游戏
    if not check.check_required_files():
        print("游戏启动终止，请先补全必要文件。")
        sys.exit(1)
    game = Game(pool.all_girls)
    game.run()