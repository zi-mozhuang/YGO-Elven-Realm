import os

# ===================== 配置替换规则（无需修改） =====================
# 规则1：替换 地点/前情/情节
OLD_TEXT1 = """*关联*
地点：
前情：
情节："""

NEW_TEXT1 = """*关联*
- 地点：
- 前情：
- 情节："""

# 规则2：替换 地点/关系/经历
OLD_TEXT2 = """*关联*
地点：
关系：
经历："""

NEW_TEXT2 = """*关联*
- 地点：
- 关系：
- 经历："""
# =================================================================

# 获取当前脚本所在文件夹
folder_path = os.getcwd()
# 统计处理数量
count = 0

# 遍历文件夹所有文件
for filename in os.listdir(folder_path):
    # 只处理markdown文件
    if filename.endswith(".md"):
        file_path = os.path.join(folder_path, filename)
        
        # 读取文件内容
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 执行两次替换
            new_content = content.replace(OLD_TEXT1, NEW_TEXT1).replace(OLD_TEXT2, NEW_TEXT2)
            
            # 如果内容发生变化，就保存文件
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1
                print(f"✅ 已处理：{filename}")
        
        # 异常处理（防止文件被占用/编码错误）
        except Exception as e:
            print(f"❌ 处理失败 {filename}：{str(e)}")

print(f"\n🎉 处理完成！总共修改了 {count} 个MD文件")