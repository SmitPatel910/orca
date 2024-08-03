import os
from openai import AzureOpenAI
from dotenv import load_dotenv

class AgentInteraction:
    def __init__(self):
        load_dotenv()
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
        )

    def init_system_prompt(self, is_complete_code):
        if is_complete_code:
            from complete_globals import SYSTEM
            input_prompt = SYSTEM.strip()
        else:
            from incomplete_globals import SYSTEM
            input_prompt = SYSTEM.strip()
        return input_prompt
    
    def init_user_prompt(self, is_complete_code):
        if is_complete_code:
            from complete_globals import USER
            input_prompt = USER.strip()
        else:
            from incomplete_globals import USER
            input_prompt = USER.strip()
        return input_prompt
    
    def apply_zero_shot(self, input_prompt):
        input_prompt = input_prompt.replace("\n<EXAMPLES>", "")
        return input_prompt
        
    def add_testing_snippet(self, input_prompt, code):
        input_prompt = input_prompt.replace("<CODE>", code)
        return input_prompt
    
    def add_symbol_table(self, input_prompt, symbol_table):
        input_prompt = input_prompt.replace("<SYMBOL_TABLE>", symbol_table)
        return input_prompt

    def remove_symbol_table(self, input_prompt):
        input_prompt = input_prompt.replace("<SYMBOL_TABLE>\n", "")
        return input_prompt
        
    def api_call(self, messages, temmprature=None, seed=None):
        if temmprature is None:
            temmprature = 0.7
        if seed is None:
            seed = 42
        response = self.client.chat.completions.create(
            model="gpt_35_turbo_16k",
            seed=seed,
            temperature=temmprature,
            timeout=120,
            messages=messages
        )

        output = response.choices[0].message.content
        
        return output, response