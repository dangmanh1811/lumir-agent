import dspy
import os
from dotenv import load_dotenv

load_dotenv()

lm = dspy.LM(
    os.getenv("MODEL_NAME"),
    api_base=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
)
dspy.configure(lm=lm)

class PlannerSignature(dspy.Signature):
    agent_name = dspy.InputField(desc="Tên của agent, chịu trách nhiệm lập kế hoạch")
    input = dspy.InputField(desc="Input chính chứa question, user_id, context_sources...")
    output = dspy.OutputField(desc="Output chứa kế hoạch và câu trả lời tổng hợp")
    plan = dspy.OutputField(desc="Kế hoạch thực hiện, dạng list chứa ditionary , mỗi dict chứa keys tên  name_plan, và keys todo")
planner_predict = dspy.Predict(PlannerSignature)
print(planner_predict(agent_name="Planner", input="Hôm nay trời đẹp không?"))