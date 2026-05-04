import os
import json
import shutil
from datetime import datetime

# ===================== 【配置区】可根据实际情况修改 =====================
TEMP_FOLDER = "temp"                # 存放MD和JSON的子文件夹
JSON_FILE = "card.json"              # temp内的JSON文件名
BACKUP_PREFIX = "temp_backup"        # 备份文件夹前缀
MD_ID_KEY = "ID"                     # MD笔记属性里的ID键名
MD_EN_KEY = "英文名"                  # MD笔记属性里的英文名键名
JSON_ID_KEY = "cid"                  # JSON里对应MD_ID_KEY的键名（cid/id二选一）
JSON_EN_KEY = "wiki_en"              # JSON里要提取的目标英文名键名
# ======================================================================

def parse_frontmatter(content):
    """
    解析Obsidian YAML Frontmatter，仅提取需要的信息，不依赖第三方库
    返回：(id_val, en_val, front_start, front_end, front_lines, en_line_idx, en_is_block)
    """
    # 找Frontmatter的边界（两个---）
    lines = content.splitlines(keepends=True)
    front_start = -1
    front_end = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "---":
            if front_start == -1:
                front_start = i
            else:
                front_end = i
                break
    if front_start == -1 or front_end == -1 or front_start >= front_end:
        return (None, None, -1, -1, [], -1, False)
    
    # 提取Frontmatter行
    front_lines = lines[front_start+1 : front_end]
    id_val = None
    en_val = None
    en_line_idx = -1
    en_is_block = False
    block_indent = ""

    # 遍历Frontmatter找目标键
    for i, line in enumerate(front_lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        
        # 找键值对的分隔符（第一个冒号）
        colon_pos = line.find(":")
        if colon_pos == -1:
            continue
        
        key = line[:colon_pos].strip()
        raw_val = line[colon_pos+1:].strip()

        # 处理ID
        if key == MD_ID_KEY:
            id_val = raw_val.strip('"').strip("'")
            continue
        
        # 处理英文名
        if key == MD_EN_KEY:
            en_line_idx = i
            # 判断是否为块标量（| |- > >-）
            if raw_val.startswith(("|", ">")):
                en_is_block = True
                # 块标量的值在下一行，找缩进的内容
                for j in range(i+1, len(front_lines)):
                    next_line = front_lines[j]
                    if next_line.strip() == "":
                        continue
                    # 记录缩进
                    block_indent = next_line[:len(next_line)-len(next_line.lstrip())]
                    en_val = next_line.strip().strip('"').strip("'")
                    break
            else:
                # 单行值
                en_val = raw_val.strip('"').strip("'")
            continue
    
    return (id_val, en_val, front_start, front_end, front_lines, en_line_idx, en_is_block)

def replace_en_in_frontmatter(front_lines, en_line_idx, en_is_block, new_en_val, MD_EN_KEY):
    """
    替换Frontmatter里的英文名，保留原格式
    返回：新的Frontmatter行列表
    """
    new_front = front_lines.copy()
    if en_is_block:
        # 块标量：保留原符号，下一行加2空格缩进（如果原没有就用2空格）
        # 先清空原块标量的后续行（如果有的话）
        j = en_line_idx + 1
        while j < len(new_front) and new_front[j].strip() == "":
            j += 1
        if j < len(new_front) and new_front[j].lstrip() != new_front[j]:
            del new_front[j]
        # 插入新值
        new_front.insert(en_line_idx + 1, f"  {new_en_val}\n")
    else:
        # 单行：直接替换
        new_front[en_line_idx] = f"{MD_EN_KEY}: {new_en_val}\n"
    return new_front

def main():
    # 统计变量
    total_md = 0
    success = 0
    skipped = 0
    failed = []

    # 1. 检查基础路径
    work_dir = os.getcwd()
    temp_path = os.path.join(work_dir, TEMP_FOLDER)
    json_path = os.path.join(temp_path, JSON_FILE)

    if not os.path.exists(temp_path):
        print(f"❌ 错误：找不到 temp 文件夹，请确保脚本在正确的位置！")
        return
    if not os.path.exists(json_path):
        print(f"❌ 错误：找不到 temp/{JSON_FILE} 文件！")
        return

    # 2. 读取并解析JSON
    print(f"📖 正在读取 {JSON_FILE} ...")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            card_data = json.load(f)
        # 把JSON转成 {ID: 卡片对象} 的字典，方便查找
        id_to_card = {}
        for card in card_data.values():
            cid = str(card.get(JSON_ID_KEY, "")).strip()
            if cid:
                id_to_card[cid] = card
        print(f"✅ 成功加载 {len(id_to_card)} 张卡片数据\n")
    except Exception as e:
        print(f"❌ 错误：解析 {JSON_FILE} 失败！\n   原因：{str(e)}")
        return

    # 3. 创建备份文件夹（带时间戳，避免覆盖）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(work_dir, f"{BACKUP_PREFIX}_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    print(f"💾 原文件将备份到：{backup_path}\n")

    # 4. 遍历temp文件夹处理MD文件
    print("🔄 开始处理MD文件...")
    for filename in os.listdir(temp_path):
        if not filename.endswith(".md"):
            continue
        total_md += 1
        md_path = os.path.join(temp_path, filename)
        backup_md_path = os.path.join(backup_path, filename)
        fail_reason = ""

        try:
            # 读取MD文件
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析Frontmatter
            id_val, en_val, front_start, front_end, front_lines, en_line_idx, en_is_block = parse_frontmatter(content)

            # 检查是否需要处理
            if id_val is None:
                fail_reason = "找不到笔记属性-ID"
                failed.append((filename, fail_reason))
                continue
            if en_val is not None and en_val.strip() != "":
                skipped += 1
                continue
            if en_line_idx == -1:
                fail_reason = "找不到笔记属性-英文名"
                failed.append((filename, fail_reason))
                continue
            
            # 在JSON中查找
            card = id_to_card.get(id_val)
            if card is None:
                fail_reason = f"JSON中找不到ID为 {id_val} 的卡片"
                failed.append((filename, fail_reason))
                continue
            new_en_val = str(card.get(JSON_EN_KEY, "")).strip()
            if not new_en_val:
                fail_reason = f"JSON中ID为 {id_val} 的卡片没有 {JSON_EN_KEY} 值"
                failed.append((filename, fail_reason))
                continue
            
            # 备份原文件
            shutil.copy2(md_path, backup_md_path)

            # 替换Frontmatter
            new_front = replace_en_in_frontmatter(front_lines, en_line_idx, en_is_block, new_en_val, MD_EN_KEY)
            # 重组整个文件内容
            lines = content.splitlines(keepends=True)
            new_lines = lines[:front_start+1] + new_front + lines[front_end:]
            new_content = "".join(new_lines)

            # 写入新文件
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            success += 1
            print(f"✅ 已补全：{filename}")

        except Exception as e:
            fail_reason = f"系统错误：{str(e)}"
            failed.append((filename, fail_reason))
            continue

    # 5. 打印统计结果
    print("\n" + "="*50)
    print(f"📊 处理完成统计：")
    print(f"   总MD文件数：{total_md}")
    print(f"   ✅ 成功补全：{success}")
    print(f"   ⏭️  跳过（已有值）：{skipped}")
    print(f"   ❌ 失败：{len(failed)}")
    if failed:
        print(f"\n   失败详情：")
        for fn, reason in failed:
            print(f"   - {fn}：{reason}")
    print(f"\n💾 原文件备份位置：{backup_path}")
    print("="*50)
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()