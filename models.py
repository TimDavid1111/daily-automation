from pydantic import BaseModel, Field


class TaskListOutput(BaseModel):
    page_title: str = Field(
        description="Format: 'DayOfWeek [MM/DD/YY]' e.g. 'Sunday [10/27/25]'"
    )
    summary: str = Field(
        description="2-3 sentences summarizing the overall context"
    )
    tasks: str = Field(
        description="Complete markdown-formatted checklist using '- [ ]' syntax"
    )

