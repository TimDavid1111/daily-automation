from anthropic import Anthropic
from models import TaskListOutput
import json

SYSTEM_PROMPT = """You are an expert at converting voice transcripts into actionable Notion task lists.

Analyze the transcript I provide and create a Notion-compatible document with this exact structure:

Structure Requirements:

Summary
* Write 2-3 sentences summarizing the overall context and what I'm working on
* Focus on the main objective or project

Tasks
* Create a checklist of all actionable tasks from the transcript
* Format as Notion checkboxes using `- [ ]` syntax
* Keep each task concise but specific (1-2 lines maximum)
* Indent sub-tasks under main tasks using tab indentation
* Preserve logical groupings and dependencies
* Order tasks by priority or natural sequence when clear from context

Guidelines:
* Extract every actionable item mentioned
* Add necessary detail for clarity without being verbose
* Use clear, action-oriented language (start with verbs)
* If a task has multiple steps, break it into a main task with indented sub-tasks
* Ensure the output renders correctly in Notion's markdown format"""


def process_transcript(client: Anthropic, transcript: str, current_date: str) -> TaskListOutput:
    """Process transcript through Claude API with structured outputs"""
    user_message = f"Current date: {current_date}\n\nTranscript:\n{transcript}"
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "task_list_output",
                "strict": True,
                "schema": TaskListOutput.model_json_schema()
            }
        }
    )
    
    # Extract JSON from response
    json_text = response.content[0].text
    data = json.loads(json_text)
    return TaskListOutput(**data)

