import os
import sys
from datetime import datetime

from loguru import logger

# 获取当前项目绝对路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

log_dir = os.path.join(root_dir, "logs")

log_file_path = f"{log_dir}/log_{datetime.now()}.log"

if not os.path.exists(log_dir): # 如果日志目录不存在则创建
    os.makedirs(log_dir)


# LOG_FILE = "translation.log" # 存储日志的文件
# Trace < Debug < Info < Success < Warning < Error < Critical

class MyLogger:
    def __init__(self):
        self.logger = logger
        # 清空所有设置
        self.logger.remove()
        # 添加控制台输出的格式, sys.stdout 为输出到屏幕；
        self.logger.add(sys.stdout,
                        level="DEBUG",
                        format="<green>{time:YYYYMMDD HH:mm:ss}</green> | "
                            "{process.name} | " # 进程名称
                            "{thread.name} | " # 线程名称
                            "<cyan>{module}</cyan>.<cyan>{function}</cyan>" # 模块名.函数名
                            ":<cyan>{line}</cyan> | " # 行号
                            "<level>{level}</level> | " # 等级
                            "<level>{message}</level>" # 日志内容
                        )

        # 输出到日志文件
        # self.logger.add(log_file_path,
        #                 level="DEBUG",
        #                 format="{time:YYYYMMDD HH:mm:ss} | "
        #                        "{process.name} | "  # 进程名称
        #                        "{thread.name} | "  # 线程名称
        #                        "{module}.{function} | >"  # 模块名.函数名
        #                        ":{line} | "  # 行号
        #                        " - {level} | "  # 等级
        #                        " - {message}",  # 日志内容
        #                 rotation="10 MB", # 日志文件生成规则 rotation="1 week" rotation="1 days"
        #                 retention="5 days", # 保留日志文件规则
        #                 #compression="zip"
        #                 )

    def get_logger(self):
        return self.logger


log = MyLogger().get_logger()

if __name__ == '__main__':
    # print(__file__)
    print(root_dir)

    log.trace("这是一条 debug 日志")
    log.debug("这是一条 debug 日志")
    log.info("这是一条 info 日志")
    log.warning("这是一条 warning 日志")
    log.error("这是一条 error 日志") # 等同 log.exception("这是一条 exception 日志")
