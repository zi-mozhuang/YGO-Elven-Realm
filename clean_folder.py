import os

def clear_files_keep_directory_structure(root_folder):
    # 检查路径是否存在
    if not os.path.exists(root_folder):
        print(f"错误：找不到路径 '{root_folder}'")
        return

    if not os.path.isdir(root_folder):
        print(f"错误：'{root_folder}' 不是一个文件夹")
        return

    files_to_delete = []
    folders_to_keep = []

    # 遍历目录树
    for root, dirs, files in os.walk(root_folder):
        # 记录遇到的文件夹（用于统计）
        for d in dirs:
            folders_to_keep.append(os.path.join(root, d))
            
        # 记录遇到的文件
        for f in files:
            file_path = os.path.join(root, f)
            files_to_delete.append(file_path)

    if not files_to_delete:
        print("目标文件夹内已经没有任何文件了（只有文件夹）。")
        return

    # --- 预览与确认 ---
    print(f"\n⚠️  即将执行操作：")
    print(f"目标路径: {root_folder}")
    print(f"├── 将删除文件总数: {len(files_to_delete)} 个")
    print(f"└── 将保留文件夹数: {len(folders_to_keep) + 1} 个 (包括根目录)")
    
    print("\n前 10 个将被删除的文件示例：")
    for f in files_to_delete[:10]:
        # 显示相对路径，更整洁
        display_path = os.path.relpath(f, root_folder)
        print(f"  - {display_path}")
    if len(files_to_delete) > 10:
        print(f"  ... (还有 {len(files_to_delete) - 10} 个文件)")

    confirm = input("\n⚠️  确认彻底清空所有文件？此操作不可恢复！(输入 yes 确认): ")
    
    if confirm.lower() != 'yes':
        print("操作已取消。")
        return

    # --- 执行删除 ---
    count = 0
    fail_count = 0
    
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            count += 1
            # 可选：如果不想看刷屏，可以把下面这行注释掉
            print(f"已删除: {os.path.relpath(file_path, root_folder)}")
        except Exception as e:
            fail_count += 1
            print(f"❌ 删除失败: {file_path} | 原因: {e}")

    print(f"\n✅ 全部完成！")
    print(f"成功删除: {count} 个文件")
    if fail_count > 0:
        print(f"失败: {fail_count} 个文件")

if __name__ == "__main__":
    print("提示：此脚本将删除指定文件夹内的所有文件，但保留所有子文件夹结构。")
    folder_input = input("请输入目标文件夹名称或路径: ")
    
    # 去除可能存在的引号
    folder_input = folder_input.strip('"').strip("'")
    
    clear_files_keep_directory_structure(folder_input)