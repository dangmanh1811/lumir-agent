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


if __name__ == '__main__':
    node_numerology_agent = NodeAgentLoader("/home/clara/manhhd/lumir-agent/config/agent_node/numerogy_v2.json")
    user_question = 'Làm thế nào để cải thiện kỹ năng code'
    
    result = node_numerology_agent(user_question)
    print(result)

