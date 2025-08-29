import json
import re
from textwrap import indent
from typing import Dict, Any, List, Literal
import dspy
from lumir.src.core.agent.client import LLMClient, LLMConfig


class DynamicSignature:

    @staticmethod
    def from_json(input_json, output_json, instruction: str = None):
        """
        """
        class_attrs = {}
        
        for field_name, description in input_json.items():
            class_attrs[field_name] = dspy.InputField(desc=description)
        
        for field_name, description in output_json.items():
            class_attrs[field_name] = dspy.OutputField(desc=description)
        
        new_class = type("AutoSignature", (dspy.Signature,), class_attrs)
        if instruction:
            new_class.__doc__ = instruction
        return new_class

class BaseAgentLoader:
    
    def __init__(self, config: Dict[str, Any]):
        """
        """
        # -------- llm config -------- #
        self.llm_config = LLMConfig()
        self.llm_client = LLMClient(self.llm_config)
        self.llm_client.client("dspy")

        # -------- agent config -------- #
        self.config = config
        self.agent = self.initialize_agent()
        # self.dynamic_signature = DynamicSignature()


    def initialize_agent(self, module_name: Literal['ChainOfThought', 'ReAct', 'Predict'] = 'ChainOfThought'):
        input_json = self.config['input']
        output_json = self.config['output']
        objective_instruction = self.config['objective_instruction']
        signature = DynamicSignature().from_json(input_json, output_json, objective_instruction)
        if module_name == 'ChainOfThought':
            return dspy.ChainOfThought(signature)
        elif module_name == 'Predict':
            return dspy.Predict(signature)
        elif module_name == 'ReAct':
            return dspy.ReAct(signature)
        
    def show_prompt_agent(self):
        " Just for testing the agent is working"
        self.run(input_data=dict())
        self.agent.inspect_history()

    def get_name_agent(self):
        " Just for testing the agent is working"
        return self.config['name']
        

    def run(self, input_data: Dict[str,any]):
        result = self.agent(**input_data)
        return result

class PenaltyContextAgent(dspy.Signature):
    """

    """
    evaluate_response : str = dspy.InputField(desc="Kiểm tra xem execute agent đã thực hiện đầy đủ các bước trong kế hoạch chưa")
    missing_steps : str = dspy.InputField(desc="Những steps nào trong plan nó bị thiếu, trả về None nếu k có bị thiếu")
    follow_plan : str = dspy.InputField(desc="Những steps nào trong plan đã được thực hiện")
    loss_context : str = dspy.OutputField(desc="Dùng để điều chỉnh response lại cho execute agent, dựa vào missing_steps, follow_plan và evaluate_response")


class NodeAgentLoader(dspy.Module):
    
    def __init__(self, config_path: str, max_attempts=3):
        super().__init__()
        self.config_path = config_path
        self.list_agents : List[BaseAgentLoader] = []
        self.max_attempts = max_attempts

        self.loss_context_agent = dspy.ChainOfThought(PenaltyContextAgent)
        with open(config_path, 'r', encoding='utf8') as f:
            configs = json.load(f)

        for idx, agent_config in enumerate(configs):
            self.list_agents.append(BaseAgentLoader(agent_config))

        # # --------- Test agent is available --------- #
        # for agent in self.list_agents:
        #     agent_name = agent.get_name_agent()
        #     print(f"--------- {agent_name} ---------")
        #     agent.show_prompt_agent()


    def load_config_json(self) -> Dict[str, Any]:
        """
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def forward(self, user_question):
        """
            context_sources: external data mà người dùng nhập vào sẽ được sử dụng ở execute agent
        """
        input_data = {
            'user_question': user_question
        }
    
        result = self.list_agents[0].run(input_data)
        plan_analyzer = result.plan
        exeternal_keywords_analyzer = result.external_keywords

        input_data['plan'] = plan_analyzer
        input_data['context_sources'] = (lambda x: x)(exeternal_keywords_analyzer) # tool calling to extract context then pass to execute
        for _ in range(self.max_attempts):
            execute_response = self.list_agents[1].run(input_data).response
            input_data['response'] = execute_response
            result = self.list_agents[2].run(input_data)
            if result.missing_steps is None: # Cái này sẽ chỉnh lại sau cho thích hợp
                break
            else:
                evaluate_response = result.evalute_response
                missing_steps = result.missing_steps
                follow_plan = result.follow_plan
                result_loss_context_agent = self.loss_context_agent(evaluate_response=evaluate_response, missing_steps=missing_steps, follow_plan=follow_plan)
                input_data['loss_context'] = result_loss_context_agent.loss_context

        return execute_response

        
class PlanEvaluator:
    def __init__(self):
        class Signature(dspy.Signature):
            """Chuyên gia đánh giá việc tuân theo kế hoạch.
            Chỉ tập trung đánh giá xem kế hoạch đã được thực hiện chính xác hay không.
            
            ĐÁNH GIÁ CHI TIẾT THEO THANG ĐIỂM 0-10:
            - 0: Hoàn toàn không tuân theo kế hoạch
            - 1: Rất ít nội dung phù hợp, chủ yếu không liên quan
            - 2: Ít nội dung phù hợp, nhiều phần không liên quan  
            - 3: Một vài điểm phù hợp nhưng thiếu nhiều chi tiết
            - 4: Cơ bản đúng hướng nhưng thiếu nhiều nội dung quan trọng
            - 5: Đủ ý chính nhưng thiếu chi tiết và cấu trúc
            - 6: Có đầy đủ ý chính nhưng thiếu sâu và chi tiết
            - 7: Đủ ý và chi tiết, nhưng thiếu một vài điểm nhỏ
            - 8: Rất tốt, đầy đủ và chi tiết, chỉ thiếu rất ít chi tiết nhỏ
            - 9: Xuất sắc, đầy đủ và chi tiết, rất sát kế hoạch
            - 10: Hoàn hảo, tuân theo kế hoạch hoàn toàn chính xác
            
            Ví dụ:
            - Kế hoạch: "Bước 1: Xác định mercado. Bước 2: Phân tích xu hướng. Bước 3: Quản lý rủi ro"
            - Answer thiếu bước 3 → điểm 5-7
            - Answer đúng cả 3 bước nhưng thiếu chi tiết → điểm 7-8
            - Answer đúng cả 3 bước và đầy đủ chi tiết → điểm 9-10"""
            question = dspy.InputField(desc="Câu hỏi gốc")
            plan = dspy.InputField(desc="Kế hoạch trả lời chi tiết")
            answer = dspy.InputField(desc="Câu trả lời đã thực hiện")
            evaluation = dspy.OutputField(desc="Đánh giá chi tiết theo thang 0-10")
            follow_plan = dspy.OutputField(desc="True nếu kế hoạch được tuân theo đầy đủ, False nếu không")
            missing_steps = dspy.OutputField(desc="Các bước trong kế hoạch chưa được thực hiện")
            score = dspy.OutputField(desc="Điểm đánh giá chính xác từ 0 đến 10")
        self.evaluate = dspy.ChainOfThought(Signature)
    
    def run(self, question, plan, answer):
        result = self.evaluate(question=question, plan=plan, answer=answer)
        
        # Fix score parsing - extract exact number from 0-10 range
        score_value = 0
        if isinstance(result.score, str):
            # First try to match single digit 0-9
            import re
            numbers = re.findall(r'\b[0-9]\b', result.score)
            if numbers:
                score_value = int(numbers[0])
            else:
                # Then try to extract number from "0/10" format
                numbers = re.findall(r'\d+', result.score)
                if numbers:
                    num = int(numbers[0])
                    # Ensure number is in 0-10 range
                    score_value = max(0, min(10, num))
        
        return {
            "follow_plan": result.follow_plan.lower() == "true",
            "score": score_value,
            "missing_steps": getattr(result, 'missing_steps', '')
        }


if __name__ == '__main__':
    node_numerology_agent = NodeAgentLoader("/home/clara/manhhd/lumir-agent/config/agent_node/numerogy_v2.json")
    user_question = 'Làm thế nào để cải thiện kỹ năng code'
    
    result = node_numerology_agent(user_question)
    print(result)

