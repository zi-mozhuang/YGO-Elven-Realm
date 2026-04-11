print("测试开始...")
import os
import json

json_file = "cards.json"

if os.path.exists(json_file):
    print(f"找到文件：{json_file}，正在读取...")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"读取成功！共包含 {len(data)} 张卡片数据。")
    print("第一张卡是：", list(data.values())[0].get("cn_name"))
else:
    print(f"错误：在当前文件夹下未找到 {json_file}！")
    print("当前路径是：", os.getcwd())

input("\n按回车键退出...")