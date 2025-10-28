from notion_client import Client
from models import TaskListOutput


def query_new_transcripts(notion: Client, database_id: str, after_time: str):
    """Query Notion database for new transcript entries after specified timestamp"""
    response = notion.databases.query(
        database_id=database_id,
        filter={
            "timestamp": "created_time",
            "created_time": {
                "after": after_time
            }
        },
        sorts=[
            {
                "timestamp": "created_time",
                "direction": "ascending"
            }
        ],
        page_size=1  # Only get the earliest new entry
    )
    return response.get("results", [])


def extract_transcript_text(page):
    """Extract transcript text from Notion page properties"""
    try:
        transcript_property = page["properties"]["Transcript"]
        # Handle rich_text property type
        if transcript_property["type"] == "rich_text":
            texts = transcript_property["rich_text"]
            return "".join([text["plain_text"] for text in texts])
        # Handle title property type (if configured differently)
        elif transcript_property["type"] == "title":
            texts = transcript_property["title"]
            return "".join([text["plain_text"] for text in texts])
        return ""
    except KeyError:
        return ""


def parse_tasks_to_blocks(tasks_markdown: str):
    """Convert markdown checklist to Notion to_do blocks"""
    blocks = []
    lines = tasks_markdown.split('\n')
    
    for line in lines:
        line = line.rstrip()
        if not line or not line.strip().startswith('- [ ]'):
            continue
            
        # Count leading tabs/spaces for indentation
        stripped = line.lstrip()
        
        # Extract task text (remove '- [ ]' prefix)
        task_text = stripped.replace('- [ ]', '').strip()
        
        if task_text:
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": task_text}
                        }
                    ],
                    "checked": False
                }
            })
            # Note: Notion API doesn't support indentation in create request
            # Sub-tasks will appear as separate blocks
    
    return blocks


def create_task_page(notion: Client, parent_page_id: str, output: TaskListOutput):
    """Create Notion page with title, summary, and tasks"""
    
    # Build blocks: Summary heading + paragraph + Tasks heading + to_do blocks
    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Summary"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": output.summary}}]
            }
        },
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "Tasks"}}]
            }
        }
    ]
    
    # Add task blocks
    task_blocks = parse_tasks_to_blocks(output.tasks)
    blocks.extend(task_blocks)
    
    # Create page
    response = notion.pages.create(
        parent={"page_id": parent_page_id},
        properties={
            "title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": output.page_title}
                    }
                ]
            }
        },
        children=blocks
    )
    
    return response

