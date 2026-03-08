import os

import pool


def check_path_exists(path, description, missing_items):
	if os.path.exists(path):
		print(f"[OK] {description}: {path}")
		return True

	print(f"[缺失] {description}: {path}")
	missing_items.append((description, path))
	return False


def check_required_files():
	missing_items = []

	check_path_exists("save", "存档目录", missing_items)
	check_path_exists(os.path.join("save", "save_overall.json"), "全局历史存档文件", missing_items)

	check_path_exists("story", "剧情目录", missing_items)
	check_path_exists(os.path.join("story", "common.json"), "共通线剧情文件", missing_items)
	check_path_exists(os.path.join("story", "girls"), "女主个人线剧情目录", missing_items)

	if not pool.all_girls:
		print("[警告] 当前角色池为空，没有可检查的女主个人线剧情文件。")
	else:
		for girl_name in pool.all_girls:
			story_path = os.path.join("story", "girls", f"{girl_name}.json")
			check_path_exists(story_path, f"{girl_name}个人线剧情文件", missing_items)

	if missing_items:
		print("\n检查未通过，以下必要文件或目录缺失：")
		for description, path in missing_items:
			print(f"- {description}: {path}")
		return False

	print("\n检查通过，必要运行文件均已配置完成。")
	return True


if __name__ == "__main__":
	check_required_files()
