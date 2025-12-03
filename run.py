from core.manager import Manager
import os
import json
import time
from datetime import datetime

# 在os中设置OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = "sk-Fukj5EU0DA0wGBHMNfhEX5IgggeuieNfKf1ExfYpDC7ELkL1"

os.makedirs("output", exist_ok=True)


prompt = """请基于以下要求开发一个完整的电商销售网页。  

产品信息与素材  
- 品牌：LYF  
- 产品：新疆香瓜子葵花子  
- 规格：30g × 10 包  
- 价格：¥16.9（原价 ¥29.9）  
- 主图链接：  
  https://gw.alicdn.com/imgextra/i3/3195305016/O1CN01FpNUtD1mvNZJLQUHu_!!3195305016.jpg_Q75.jpg_.webp

4P 营销要求（必须实现）
1) 产品（外观图、规格、卖点、评论区、详情展示）
2) 价格（现价、原价、折扣展示、券后价逻辑）
3) 渠道（清晰的购买入口与购物流程）
4) 促销（限时倒计时、热销标签、库存提醒、优惠券）

UI 风格  
- 对标天猫移动端视觉规范
- 春节红主色调（#E4393C 或类似）
- 动效与交互体现节日感、紧迫感与愉悦感

设备与布局要求  
- 页面宽度950px  
- 顶部保留状态区和导航栏结构（如返回、购物车图标等）。  
- 不需要使用占位符，来体现插入图片(如果没有图片的链接，则禁止使用图片)。

功能规范（必须实现）
A. 购物模块  
- 数量增减、加入购物车、立即购买  
- localStorage 保存购物车数据  
- 购物车侧栏展开/关闭  
- 购物车商品编辑、删除、结算总价计算  

B. 促销模块  
- 限时倒计时（自动更新 UI）  
- 库存动态显示（库存减少逻辑）  
- 领券中心（用户可领券，并用于结算减免）  

C. 内容展示  
- 商品评价（评分+评论列表，含表情符号与图片示例）  
- 商品详情折叠与展开  


创新功能（自定义添加1个以上的创新功能）


 输出格式:直接输出完整 HTML 文件代码 (只需要输出HTML)
"""

combinations = [(op, cp) for op in (True, False) for cp in (True, False)]

model = "OPENAI"

runtime_log_path = "output/runtime_log.txt"

for tmp_i in range(1, 5):
    print(tmp_i)
    json_folder = "output/json"
    resp_folder = "output/resp"
    os.makedirs(json_folder, exist_ok=True)

    for op, cp in combinations:
        start_time = time.time()  # ⏱ 开始计时

        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        op_value = 1 if op else 0
        cp_value = 1 if cp else 0
        suffix = f"{timestamp}__OP-{op_value}_CP-{cp_value}"
        print(suffix)

        manager = Manager(cp=cp, sp=op)
        html, resp = manager.run(prompt)
        # 保存resp日志
        resp_file_path = f"{resp_folder}/{model}_{tmp_i}##过程_{suffix}.json"
        with open(resp_folder, "w", encoding="utf-8") as log_file:
            json.dump(resp, log_file, ensure_ascii=False, indent=2)



        # 保存JSON日志
        json_file_path = f"{json_folder}/{model}_{tmp_i}##messages_{suffix}.json"
        with open(json_file_path, "w", encoding="utf-8") as log_file:
            json.dump(manager.bus.dump(), log_file, ensure_ascii=False, indent=2)

        # 保存HTML输出
        html_file_path = f"output/{model}_{tmp_i}##index_{suffix}.html"
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html)

        end_time = time.time()  # ⏱ 结束计时
        duration = end_time - start_time

        # 记录运行时长到 txt 文件
        with open(runtime_log_path, "a", encoding="utf-8") as rt:
            rt.write(f"{suffix}, Iter: {tmp_i}, Duration: {duration:.2f} seconds\n")

        print(f"网页已生成：{html_file_path}")
        print(f"运行时间记录：{duration:.2f} 秒\n")
