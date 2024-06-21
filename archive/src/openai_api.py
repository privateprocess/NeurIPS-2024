from openai import OpenAI
from typing import *
import asyncio

class Client:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    async def check_moderation(self, expression):
        moderation_response = self.client.moderations.create(input=expression)
        return moderation_response.results[0]
        
    async def chat_response(self, system_prompt, user_request):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_request},
        ]
        response = self.client.chat.completions.create(
            model='gpt-3.5-turbo', messages=messages, temperature=0.0
        )
        return response.choices[0]

    async def execute_chat(self, system_prompt, user_request):
        # Create tasks for moderation and chat response
        moderation_task = asyncio.create_task(self.check_moderation(user_request))
        chat_task = asyncio.create_task(self.chat_response(system_prompt, user_request))

        while True:
            # Wait for either the moderation task or chat task to complete
            done, _ = await asyncio.wait(
                [moderation_task, chat_task], return_when=asyncio.FIRST_COMPLETED
            )

            # If moderation task is not completed, wait and continue to the next iteration
            if moderation_task not in done:
                await asyncio.sleep(0.1)
                continue

            # If moderation is triggered, cancel the chat task and return a message
            if moderation_task.result().flagged == True:
                chat_task.cancel()
                return {
                    "flagged": True,
                    "moderation_response": moderation_task.result(),
                    "response": "",
                }

            # If chat task is completed, return the chat response
            if chat_task in done:
                print(chat_task.result().finish_reason)
                return {
                    "flagged": False,
                    "response": chat_task.result().message.content,
                }

            # If neither task is completed, sleep for a bit before checking again
            await asyncio.sleep(0.1)