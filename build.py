import os
import shutil

# 创建必要的目录结构
os.makedirs("build/data", exist_ok=True)
os.makedirs("build/config", exist_ok=True)

# 复制配置文件
shutil.copy("cvy_pipeline_config.json", "build/")
shutil.copy("hsv_pipeliner_config.json", "build/")

# 复制config目录下的模型文件
for file in os.listdir("config"):
    shutil.copy(os.path.join("config", file), os.path.join("build/config", file))

# 运行PyInstaller
os.system("pyinstaller --noconfirm --clean --name=松科变色立木检测系统 --icon=app_icon.ico "
          "--add-data build/cvy_pipeline_config.json;. "
          "--add-data build/hsv_pipeliner_config.json;. "
          "--add-data build/config;config "
          "--hidden-import PySide6.QtSvg "
          "--hidden-import PySide6.QtXml "
          "--windowed Qt/main.py")

# 清理临时文件
shutil.rmtree("build", ignore_errors=True)