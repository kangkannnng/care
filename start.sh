#!/bin/bash

# 用 Python 提取 model 名称
MODEL_NAME=$(python3 -c "
import config
print(config.model_name)
")

# 生成日志文件名
LOG_FILE="log/${MODEL_NAME}_$(date +'%Y%m%d_%H%M%S').log"

echo "Running workflow.py with model: $MODEL_NAME, logging to: $LOG_FILE"
python workflow.py | tee -a "$LOG_FILE"