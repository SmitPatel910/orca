import os
from openai import AzureOpenAI
from dotenv import load_dotenv, find_dotenv

class AgentInteraction:
    def __init__(self):
        # Load environment variables from a .env file
        load_dotenv(find_dotenv())

        # Initialize Azure OpenAI client using environment variables
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
        )

    def init_system_prompt(self, is_complete_code):
        '''Initialize the system prompt based on the code completeness flag.

        Args:
            is_complete_code (bool): Determines whether to use the complete or incomplete system prompt.

        Returns:
            str: The system prompt based on the code completeness flag.
        '''

        if is_complete_code:
            # Import system prompt for complete code
            from complete_globals import SYSTEM
            input_prompt = SYSTEM.strip()
        else:
            # Import system prompt for incomplete code
            from incomplete_globals import SYSTEM
            input_prompt = SYSTEM.strip()
        return input_prompt
    
    def init_user_prompt(self, is_complete_code):
        '''Initialize the user prompt based on the code completeness flag.

        Args:
            is_complete_code (bool): Determines whether to use the complete or incomplete user prompt.

        Returns:
            str: The user prompt based on the code completeness flag.
        '''
        if is_complete_code:
            # Import user prompt for complete code
            from complete_globals import USER
            input_prompt = USER.strip()
        else:
            # Import user prompt for incomplete code
            from incomplete_globals import USER
            input_prompt = USER.strip()
        return input_prompt
    
    def apply_zero_shot(self, input_prompt):
        '''Apply zero-shot prompt modification by removing the <EXAMPLES> tag in the input prompt.

        Args:
            input_prompt (str): The input prompt to modify.

        Returns:
            str: The modified prompt without the <EXAMPLES> tag.
        '''
        input_prompt = input_prompt.replace("\n<EXAMPLES>", "")
        return input_prompt
        
    def add_testing_snippet(self, input_prompt, code):
        '''Add a code snippet to the input prompt by replacing the <CODE> placeholder.

        Args:
            input_prompt (str): The input prompt containing a <CODE> placeholder.
            code (str): The code snippet to insert into the prompt.

        Returns:
            str: The modified prompt with the code snippet included.
        '''
        input_prompt = input_prompt.replace("<CODE>", code)
        return input_prompt
            
    def api_call(self, messages, model=None, temmprature=None, seed=None, timeOut=None):
        '''Make an API call to the Azure OpenAI chat completion endpoint.

        This function sends a list of messages to the specified model using Azure OpenAI's 
        chat completions API and retrieves the generated response. 
        Default values are used for optional parameters if they are not provided.

        Arguments:
            messages (list): A list of messages to send to the OpenAI model.
            model (str, optional): The name of the OpenAI model to use (default: "gpt_35_turbo_16k").
            timeOut (int, optional): The timeout in seconds for the API request (default: 120).
            temmprature (float, optional): The temperature for response generation to control randomness (default: 0.7).
            seed (int, optional): The seed for deterministic behavior in the model (default: 42).

        Returns:
            tuple: A tuple containing:
                - output (str): The generated response content.
                - response (object): The raw API response object from Azure OpenAI.
        '''

        # Set default values if not provided
        if temmprature is None:
            temmprature = 0.7
        if seed is None:
            seed = 42
        if model is None:
            model = "gpt_35_turbo_16k"
        if timeOut is None:
            timeOut = 120

        response = self.client.chat.completions.create(
            model= model,
            seed=seed,
            temperature=temmprature,
            timeout=timeOut,
            messages=messages
        )

        output = response.choices[0].message.content

        return output, response