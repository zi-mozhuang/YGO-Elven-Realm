import json
import requests
import os
import time

# 可自定义配置项
JSON_FILE = "cards.json"  # 全卡数据文件路径
SAVE_FOLDER = "./ygocard_images"  # 卡图临时保存文件夹
CDN_URL = "https://cdn.233.momobako.com/ygopro/pics/{card_id}.jpg"
REQUEST_DELAY = 0.5  # 请求间隔（秒），请勿调太小
MAX_RETRY = 3  # 单张卡图下载失败重试次数

# 创建保存文件夹
os.makedirs(SAVE_FOLDER, exist_ok=True)

# 读取全卡数据
with open(JSON_FILE, "r", encoding="utf-8") as f:
    card_data = json.load(f)

# 遍历下载逻辑
total = len(card_data)
success = 0
failed_list = []

print(f"共找到 {total} 张卡片，开始下载...")
for cid, card_info in card_data.items():
    card_id = card_info.get("id")
    card_name = card_info.get("cn_name", "未知卡片")
    
    if not card_id:
        failed_list.append(f"cid:{cid}_{card_name}（无卡密ID）")
        continue

    # --- 修改点：这里直接使用 card_id (卡密) 作为文件名 ---
    save_path = os.path.join(SAVE_FOLDER, f"{card_id}.jpg")
    download_url = CDN_URL.format(card_id=card_id)
    retry_count = 0

    # 跳过已下载的文件
    if os.path.exists(save_path):
        print(f"已存在：{card_id}_{card_name}，跳过")
        success += 1
        continue

    # 下载重试逻辑
    while retry_count < MAX_RETRY:
        try:
            response = requests.get(download_url, timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as img_file:
                    img_file.write(response.content)
                print(f"下载成功：{card_id}_{card_name} | 进度：{success+1}/{total}")
                success += 1
                break
            else:
                retry_count += 1
                print(f"下载失败（状态码{response.status_code}）：{card_id}_{card_name}，重试{retry_count}/{MAX_RETRY}")
        except Exception as e:
            retry_count += 1
            print(f"下载异常：{card_id}_{card_name}，错误：{str(e)}，重试{retry_count}/{MAX_RETRY}")
        time.sleep(REQUEST_DELAY)

    if retry_count >= MAX_RETRY:
        failed_list.append(f"{card_id}_{card_name}")
        print(f"最终失败：{card_id}_{card_name}")
    time.sleep(REQUEST_DELAY)

# 下载完成统计
print("\n"+"="*50)
print(f"下载任务完成！总计：{total} | 成功：{success} | 失败：{len(failed_list)}")
if failed_list:
    print("失败卡片列表：")
    for item in failed_list:
        print(f"- {item}")