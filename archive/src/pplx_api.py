from openai import OpenAI
from json import loads
from typing import *
import asyncio

class Client:
    def __init__(self, api_key: str, model="llama-3-70b-instruct") -> None:
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.perplexity.ai")
        self.model = model
        
    async def chat_response(self, system_prompt, content):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0
        )
        return response.choices[0]
    
    async def custom_moderation(self, content, parameters):
        prompt = f"""Please assess the following content for any inappropriate material. You should base your assessment on the given parameters.
        Your answer should be in json format only with the following fields: 
            - flagged: a boolean indicating whether the content is flagged for any of the categories in the parameters
            - reason: a string explaining the reason for the flag, if any
            - parameters: a dictionary of the parameters used for the assessment and their values
        Parameters: {parameters}\n\nContent:\n{content}\n\nAssessment:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "You are a content moderation assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the assessment from the response
        assessment = response.choices[0].message.content
        
        return assessment

    async def execute_chat(self, system_prompt, content, parameters):
        # Create tasks for moderation and chat response
        moderation_task = asyncio.create_task(self.custom_moderation(parameters, content))
        chat_task = asyncio.create_task(self.chat_response(system_prompt, content))

        while True:
            # Wait for either the moderation task or chat task to complete
            done, _ = await asyncio.wait(
                [moderation_task, chat_task], return_when=asyncio.ALL_COMPLETED
            )

            if done:
                return {
                    "moderation_response": moderation_task.result(),
                    "response": chat_task.result().message.content,
                }

            # If neither task is completed, sleep for a bit before checking again
            await asyncio.sleep(0.1)

        