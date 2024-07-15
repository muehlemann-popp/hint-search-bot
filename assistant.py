from openai import NOT_GIVEN, NotGiven, OpenAI
from openai.types.beta.thread import Thread
from openai.types.beta.threads import Message, RunStatus

from settings import assistant_id, openai_api_key

client = OpenAI(api_key=openai_api_key, organization="org-SPulFD0HNP5YXbJNABRYv3JN")

assistant = client.beta.assistants.retrieve(assistant_id)


def create_thread():
    return client.beta.threads.create()


def restore_messages(messages, thread: Thread):
    for message in messages:
        client.beta.threads.messages.create(thread.id, **message)


def query(prompt: str, thread: Thread) -> list[Message] | RunStatus:
    full_prompt = f"""
    In all available files, find tickets related to the following search query inside <query> markers.
    <query>{prompt}<query>
    
    The output should be in the format inside <output> markers:

    <output>
    Link: <link to the ticket><br/>
    Name: <ticket name><br/>
    Description: <short summary ticket description><br/>
    Status: <status><br/>
    <br/>
    <br/>
    <output>

    Return as many tickets as you can find.
    Do not include file citations in the output.
    Do not wrap the output in any markers.
    """
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=full_prompt,
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Please address the user as Jane Doe. The user has a premium account.",
    )

    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
        messages = list(messages)
        messages.reverse()
        return messages
    else:
        return run.status
