"""
Notion Webhook Server
Receives real-time updates from Notion when database entries are created/updated
"""
import os
import hmac
import hashlib
import json
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from notion_client import Client as NotionClient
from anthropic import Anthropic
from notion_api import extract_transcript_text, create_task_page
from claude_client import process_transcript
from utils import get_formatted_date

# Load environment
load_dotenv()

app = FastAPI(title="Notion Transcript Automation")

# Initialize clients
notion = NotionClient(auth=os.getenv("NOTION_TOKEN"))
claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Configuration
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


def verify_signature(request_body: bytes, signature: str) -> bool:
    """
    Verify that the webhook request came from Notion using HMAC-SHA256
    """
    if not WEBHOOK_SECRET:
        # If no secret is configured, skip validation (not recommended for production)
        print("⚠️  Warning: WEBHOOK_SECRET not set, skipping signature validation")
        return True
    
    # Calculate expected signature
    calculated_signature = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(calculated_signature, signature)


async def process_transcript_async(page_id: str):
    """
    Background task to process a transcript from a Notion page
    """
    try:
        print(f"📝 Processing page: {page_id}")
        
        # Retrieve the page from Notion
        page = notion.pages.retrieve(page_id=page_id)
        
        # Extract transcript text
        transcript_text = extract_transcript_text(page)
        
        if not transcript_text:
            print(f"⚠️  No transcript text found in page {page_id}")
            return
        
        print(f"✓ Found transcript ({len(transcript_text)} chars)")
        
        # Get formatted date for page title
        page_title_date, full_date = get_formatted_date()
        
        # Process with Claude
        print("🤖 Sending to Claude API...")
        structured_output = process_transcript(claude, transcript_text, full_date)
        
        # Override page title with formatted date
        structured_output.page_title = page_title_date
        
        # Create Notion page
        print("📄 Creating Notion page...")
        created_page = create_task_page(notion, PARENT_PAGE_ID, structured_output)
        
        print(f"✅ Created page: {structured_output.page_title}")
        print(f"🔗 URL: {created_page['url']}")
        
    except Exception as e:
        print(f"❌ Error processing transcript: {e}")
        import traceback
        traceback.print_exc()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Notion Transcript Automation",
        "version": "2.0.0-webhooks"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "notion_configured": bool(os.getenv("NOTION_TOKEN")),
        "claude_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "webhook_secret_configured": bool(WEBHOOK_SECRET),
        "parent_page_configured": bool(PARENT_PAGE_ID),
        "database_configured": bool(DATABASE_ID)
    }


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint to receive events from Notion
    """
    # Get raw body for signature verification
    body_bytes = await request.body()
    body = json.loads(body_bytes.decode("utf-8"))
    
    # Get signature from headers
    signature = request.headers.get("X-Notion-Signature", "")
    
    # Verify signature
    if not verify_signature(body_bytes, signature):
        print("❌ Invalid signature - request rejected")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Handle verification challenge (initial webhook setup)
    if "verification_token" in body:
        print("🔐 Received verification token")
        verification_token = body["verification_token"]
        print(f"Token: {verification_token}")
        print("⚠️  Copy this token to your Notion webhook settings to complete verification!")
        return JSONResponse(content={"received": True})
    
    # Handle actual webhook events
    event_type = body.get("type")
    
    print(f"\n📨 Received webhook event: {event_type}")
    
    # Process data_source.content_updated events (when database content changes)
    if event_type == "data_source.content_updated":
        # Extract entity and data from the event
        entity = body.get("entity", {})
        event_data = body.get("data", {})
        
        # DEBUG: Log the full payload structure
        print(f"🔍 DEBUG - Full event data: {json.dumps(body, indent=2)}")
        
        # Verify this is a data_source entity
        if entity.get("type") == "data_source":
            data_source_id = entity.get("id", "").replace("-", "")
            target_db_id = DATABASE_ID.replace("-", "")
            
            # DEBUG: Log entity info
            print(f"🔍 DEBUG - Data Source ID: {data_source_id}")
            print(f"🔍 DEBUG - Target DATABASE_ID: {target_db_id}")
            
            # Only process events from our target database
            if data_source_id == target_db_id:
                print(f"✓ Event is from target database")
                
                # Extract the updated blocks (pages that were added/updated)
                updated_blocks = event_data.get("updated_blocks", [])
                
                if updated_blocks:
                    print(f"✓ Found {len(updated_blocks)} updated block(s)")
                    
                    # Process each updated block (page) in the background
                    for block in updated_blocks:
                        block_id = block.get("id")
                        block_type = block.get("type")
                        
                        print(f"🔍 DEBUG - Block ID: {block_id}, Type: {block_type}")
                        
                        if block_id and block_type == "block":
                            # The block ID is actually a page ID when it's a database child
                            print(f"✓ Processing block as page: {block_id}")
                            background_tasks.add_task(process_transcript_async, block_id)
                else:
                    print(f"ℹ️  No updated blocks in event")
            else:
                print(f"ℹ️  Event from different database (ID: {data_source_id}), ignoring")
        else:
            print(f"ℹ️  Event entity is not a data_source, ignoring")
    else:
        print(f"ℹ️  Event type '{event_type}' not handled")
    
    return JSONResponse(content={"received": True})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 Starting webhook server on port {port}")
    print(f"📍 Webhook URL: http://localhost:{port}/webhook")
    uvicorn.run(app, host="0.0.0.0", port=port)

