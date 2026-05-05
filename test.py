import os
import re
import shutil
from datetime import datetime

# ===================== 【配置区】可根据实际情况修改 =====================
TARGET_FOLDER = "."                  # 目标文件夹，"." 表示当前文件夹
BACKUP_PREFIX = "md_backup"          # 备份文件夹前缀
CATEGORY_KEY = "分类"                 # 笔记属性里的分类键名
EXTRA_KEY = "连接方向/灵摆值"         # 笔记属性里的连接方向键名
KEYWORD = "连接"                      # 分类里要匹配的关键词
# ======================================================================

# 游戏王常见箭头/方向词列表
ARROW_CHARS = [
    "↑", "↓", "←", "→", "↖", "↗", "↙", "↘",
    "上", "下", "左", "右", "左上", "右上", "左下", "右下"
]

def wrap_arrows(text):
    if not text:
        return text
    cleaned = text.replace("[", "").replace("]", "")
    sorted_arrows = sorted(ARROW_CHARS, key=lambda x: -len(x))
    result = cleaned
    for arrow in sorted_arrows:
        if arrow in result:
            result = result.replace(arrow, f"[{arrow}]")
    return result

def parse_frontmatter(content):
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
        return (False, None, -1, -1, -1, [], False)
    
    front_lines = lines[front_start+1 : front_end]
    has_keyword = False
    extra_val = None
    extra_line_idx = -1
    extra_is_quoted = False
    
    for i, line in enumerate(front_lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        colon_pos = line.find(":")
        if colon_pos == -1:
            continue
        key = line[:colon_pos].strip()
        val_after_colon = line[colon_pos+1:].strip()
        
        if key == CATEGORY_KEY:
            if KEYWORD in val_after_colon:
                has_keyword = True
            continue
        if key == EXTRA_KEY:
            extra_line_idx = i
            if val_after_colon.startswith('"') and val_after_colon.endswith('"'):
                extra_is_quoted = True
                extra_val = val_after_colon[1:-1]
            else:
                extra_val = val_after_colon.strip('"').strip("'")
            continue
    return (has_keyword, extra_val, extra_line_idx, front_start, front_end, front_lines, extra_is_quoted)

def main():
    total_md = 0
    success = 0
    skipped = 0
    failed = []

    # 1. 路径检查
    work_dir = os.getcwd()
    target_path = os.path.join(work_dir, TARGET_FOLDER) if TARGET_FOLDER != "." else work_dir
    if not os.path.exists(target_path):
        print(f"❌ 错误：找不到目标文件夹 {target_path}！")
        return

    # 2. 创建备份文件夹（先创建，这样后面才能排除它）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder_name = f"{BACKUP_PREFIX}_{timestamp}"
    backup_path = os.path.join(work_dir, backup_folder_name)
    os.makedirs(backup_path, exist_ok=True)
    print(f"💾 原文件将备份到：{backup_path}")
    print(f"⚠️  已自动排除备份文件夹，避免递归循环\n")

    # 3. 【核心修复】递归遍历 + 源头排除备份文件夹
    print("🔄 开始递归处理所有子文件夹...")
    for root, dirs, files in os.walk(target_path, topdown=True):
        # 【关键代码】在 topdown 模式下，修改 dirs 列表可以直接排除子文件夹
        # 这里我们把备份文件夹从 dirs 里移除，os.walk 就不会进去了
        dirs[:] = [d for d in dirs if not d.startswith(BACKUP_PREFIX)]
        
        for filename in files:
            if not filename.endswith(".md"):
                continue
            
            total_md += 1
            md_full_path = os.path.join(root, filename)
            md_relative_path = os.path.relpath(md_full_path, target_path)
            
            # 计算备份路径（保持原结构）
            md_backup_rel_dir = os.path.relpath(root, target_path)
            md_backup_dir = os.path.join(backup_path, md_backup_rel_dir)
            os.makedirs(md_backup_dir, exist_ok=True)
            md_backup_path = os.path.join(md_backup_dir, filename)
            
            fail_reason = ""
            try:
                with open(md_full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                has_keyword, extra_val, extra_line_idx, front_start, front_end, front_lines, extra_is_quoted = parse_frontmatter(content)

                if not has_keyword:
                    skipped += 1
                    continue
                if extra_line_idx == -1:
                    fail_reason = f"缺少属性「{EXTRA_KEY}」"
                    failed.append((md_relative_path, fail_reason))
                    continue
                if not extra_val:
                    fail_reason = f"属性「{EXTRA_KEY}」为空"
                    failed.append((md_relative_path, fail_reason))
                    continue
                
                processed_val = wrap_arrows(extra_val)
                shutil.copy2(md_full_path, md_backup_path)
                
                new_front = front_lines.copy()
                new_front[extra_line_idx] = f"{EXTRA_KEY}: \"{processed_val}\"\n"
                lines = content.splitlines(keepends=True)
                new_content = "".join(lines[:front_start+1] + new_front + lines[front_end:])
                
                with open(md_full_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                success += 1
                print(f"✅ [{success}] 已处理：{md_relative_path}")
                if extra_val != processed_val:
                    print(f"   箭头处理：{extra_val} → {processed_val}")

            except Exception as e:
                fail_reason = f"系统错误：{str(e)}"
                failed.append((md_relative_path, fail_reason))
                continue

    # 4. 统计
    print("\n" + "="*60)
    print(f"📊 处理完成统计：")
    print(f"   总MD文件数：{total_md}")
    print(f"   ✅ 成功处理：{success}")
    print(f"   ⏭️  跳过（非连接怪兽）：{skipped}")
    print(f"   ❌ 失败：{len(failed)}")
    if failed:
        print(f"\n   失败详情：")
        for fn, reason in failed:
            print(f"   - {fn}：{reason}")
    print(f"\n💾 原文件备份位置：{backup_path}")
    print("="*60)
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()