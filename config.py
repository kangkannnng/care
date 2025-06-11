from autogen import LLMConfig

# 数据集路径
dataset_path = "/home/kangkang/code/care/data"

# 模型配置

model_name = "deepseek"
llm_config = LLMConfig(
    api_type="deepseek",
    model="deepseek-chat",
    api_key="sk-511f3246640241bd850af659c73283bd",
    base_url="https://api.deepseek.com/v1"
)


# model_name = "llama3.1"
# llm_config = LLMConfig(model=model_name, api_type="ollama", hide_tools="if_all_run")