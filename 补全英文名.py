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
JSON_ID_KEY = "cid"                  # JSON里对应MD_ID_KEY的键名
JSON_EN_KEY = "wiki_en"              # JSON里要提取的目标英文名键名
# ======================================================================

def parse_frontmatter(content):
    """
    重写：更健壮的Obsidian YAML Frontmatter解析器
    专门优化了块标量空值的识别
    """
    lines = content.splitlines(keepends=True)
    front_start = -1
    front_end = -1
    
    # 1. 找Frontmatter边界
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "---":
            if front_start == -1:
                front_start = i
            else:
                front_end = i
                break
    if front_start == -1 or front_end == -1 or front_start >= front_end:
        return (None, None, -1, -1, [], -1, False, "无有效Frontmatter")
    
    front_lines = lines[front_start+1 : front_end]
    id_val = None
    en_val = None
    en_line_idx = -1
    en_is_block = False
    en_raw_line = ""
    
    # 2. 遍历解析
    i = 0
    while i < len(front_lines):
        line = front_lines[i]
        stripped = line.strip()
        
        # 跳过空行和注释
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        
        # 找键值对
        colon_pos = line.find(":")
        if colon_pos == -1:
            i += 1
            continue
        
        key = line[:colon_pos].strip()
        val_after_colon = line[colon_pos+1:].strip()
        
        # 处理ID
        if key == MD_ID_KEY:
            id_val = val_after_colon.strip('"').strip("'")
            i += 1
            continue
        
        # 处理英文名（核心修复部分）
        if key == MD_EN_KEY:
            en_line_idx = i
            en_raw_line = line
            en_is_block = val_after_colon.startswith(("|", ">"))
            
            if en_is_block:
                # 【核心修复】块标量处理：专门找下一行的非空缩进内容
                en_val = ""  # 默认空
                j = i + 1
                # 跳过中间的空行
                while j < len(front_lines) and front_lines[j].strip() == "":
                    j += 1
                # 检查下一行是否有缩进内容
                if j < len(front_lines):
                    candidate_line = front_lines[j]
                    # 如果有缩进（不是顶格），说明是块标量的值
                    if candidate_line.lstrip() != candidate_line:
                        en_val = candidate_line.strip().strip('"').strip("'")
            else:
                # 单行值处理
                en_val = val_after_colon.strip('"').strip("'")
            
            i += 1
            continue
        
        i += 1
    
    # 3. 返回结果和状态
    status = "正常"
    if id_val is None:
        status = f"缺少属性「{MD_ID_KEY}」"
    elif en_line_idx == -1:
        status = f"缺少属性「{MD_EN_KEY}」"
    
    return (id_val, en_val, front_start, front_end, front_lines, en_line_idx, en_is_block, status)

def replace_en_in_frontmatter(front_lines, en_line_idx, en_is_block, new_en_val, MD_EN_KEY):
    """
    替换Frontmatter里的英文名，完美保留原格式
    """
    new_front = front_lines.copy()
    
    if en_is_block:
        # 块标量模式
        # 1. 先清空原块标量的后续行（如果有的话）
        j = en_line_idx + 1
        # 跳过空行
        while j < len(new_front) and new_front[j].strip() == "":
            j += 1
        # 删除有缩进的旧值行
        if j < len(new_front) and new_front[j].lstrip() != new_front[j]:
            del new_front[j]
        
        # 2. 插入新值（保持2空格缩进）
        new_front.insert(en_line_idx + 1, f"  {new_en_val}\n")
    else:
        # 单行模式：直接替换
        new_front[en_line_idx] = f"{MD_EN_KEY}: {new_en_val}\n"
    
    return new_front

def main():
    total_md = 0
    success = 0
    skipped = 0
    failed = []
    skipped_details = []

    # 1. 路径检查
    work_dir = os.getcwd()
    temp_path = os.path.join(work_dir, TEMP_FOLDER)
    json_path = os.path.join(temp_path, JSON_FILE)

    if not os.path.exists(temp_path):
        print(f"❌ 错误：找不到 temp 文件夹！")
        return
    if not os.path.exists(json_path):
        print(f"❌ 错误：找不到 temp/{JSON_FILE}！")
        return

    # 2. 读取JSON
    print(f"📖 正在读取 {JSON_FILE} ...")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            card_data = json.load(f)
        id_to_card = {}
        for card in card_data.values():
            cid = str(card.get(JSON_ID_KEY, "")).strip()
            if cid:
                id_to_card[cid] = card
        print(f"✅ 成功加载 {len(id_to_card)} 张卡片\n")
    except Exception as e:
        print(f"❌ JSON解析失败：{str(e)}")
        return

    # 3. 备份文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(work_dir, f"{BACKUP_PREFIX}_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    print(f"💾 原文件备份到：{backup_path}\n")

    # 4. 处理MD文件
    print("🔄 开始处理...")
    for filename in os.listdir(temp_path):
        if not filename.endswith(".md"):
            continue
        total_md += 1
        md_path = os.path.join(temp_path, filename)
        backup_md_path = os.path.join(backup_path, filename)

        try:
            # 读取文件
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析Frontmatter
            id_val, en_val, front_start, front_end, front_lines, en_line_idx, en_is_block, status = parse_frontmatter(content)

            # 基础检查
            if status != "正常":
                failed.append((filename, status))
                continue
            
            # 【核心修复】严格判断是否为空
            is_en_empty = (en_val is None) or (en_val.strip() == "")
            
            if not is_en_empty:
                skipped += 1
                skipped_details.append((filename, f"英文名已有值：{en_val[:30]}..."))
                continue
            
            # 查找JSON
            card = id_to_card.get(id_val)
            if card is None:
                failed.append((filename, f"JSON中无ID：{id_val}"))
                continue
            
            new_en_val = str(card.get(JSON_EN_KEY, "")).strip()
            if not new_en_val:
                failed.append((filename, f"JSON中ID {id_val} 无 {JSON_EN_KEY}"))
                continue
            
            # 备份并替换
            shutil.copy2(md_path, backup_md_path)
            new_front = replace_en_in_frontmatter(front_lines, en_line_idx, en_is_block, new_en_val, MD_EN_KEY)
            lines = content.splitlines(keepends=True)
            new_content = "".join(lines[:front_start+1] + new_front + lines[front_end:])
            
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            success += 1
            print(f"✅ [{success}] 补全：{filename}")

        except Exception as e:
            failed.append((filename, f"系统错误：{str(e)}"))
            continue

    # 5. 详细统计
    print("\n" + "="*60)
    print(f"📊 最终统计：")
    print(f"   总文件数：{total_md}")
    print(f"   ✅ 成功补全：{success}")
    print(f"   ⏭️  跳过（已有值）：{skipped}")
    print(f"   ❌ 失败：{len(failed)}")
    
    if skipped_details:
        print(f"\n   📋 跳过详情（前10个）：")
        for fn, reason in skipped_details[:10]:
            print(f"   - {fn}：{reason}")
        if len(skipped_details) > 10:
            print(f"   ... 还有 {len(skipped_details)-10} 个")
    
    if failed:
        print(f"\n   ❌ 失败详情：")
        for fn, reason in failed:
            print(f"   - {fn}：{reason}")
    
    print(f"\n💾 备份位置：{backup_path}")
    print("="*60)
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()