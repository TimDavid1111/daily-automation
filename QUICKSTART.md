# Quick Start Guide — Webhook Version 2.0

**🎉 New in v2.0: Real-time webhook-based processing!**

This version uses Notion webhooks for instant processing instead of polling. Your transcripts are processed within seconds of being added to Notion.

## Prerequisites

- A Notion account with a workspace
- An Anthropic (Claude) API account
- A Render account (free tier is fine)

## Step 1: Get Your Notion Credentials

### Create a Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "+ New integration"
3. Name it (e.g., "Voice Transcript Automation")
4. Select your workspace
5. Click "Submit"
6. Copy the "Internal Integration Token" (starts with `secret_`)

### Get Your Database ID

1. Open your "Raw Transcripts" database in Notion
2. Click "Share" → Add your integration
3. Copy the database URL: `https://www.notion.so/workspace/[DATABASE_ID]?v=...`
4. The DATABASE_ID is the 32-character string (with dashes removed if present)

### Get Your Parent Page ID

1. Open the page where you want task pages created
2. Click "Share" → Add your integration
3. Copy the page URL: `https://www.notion.so/workspace/[PAGE_ID]`
4. The PAGE_ID is the 32-character string

## Step 2: Get Your Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys"
4. Create a new key
5. Copy the key (starts with `sk-ant-`)

## Step 3: Deploy to Render

### Create a Render Account

1. Go to https://render.com/
2. Sign up with GitHub (recommended for easy deployment)
3. The **free tier is perfect** for this project

### Deploy Your Application

**Option A: Deploy from GitHub (Recommended)**

1. Fork or push this repository to your GitHub account

2. In Render dashboard, click **"New +"** → **"Web Service"**

3. Connect your GitHub repository

4. Render will auto-detect the `render.yaml` configuration

5. Click **"Apply"** to create the service

**Option B: Deploy from Git URL**

1. In Render dashboard, click **"New +"** → **"Web Service"**

2. Choose **"Public Git repository"**

3. Enter your repository URL

4. Configure manually:
   - **Name**: `notion-automation`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install uv && uv sync`
   - **Start Command**: `uv run uvicorn webhook_server:app --host 0.0.0.0 --port $PORT`

### Configure Environment Variables

In your Render service settings, add these environment variables:

```env
NOTION_TOKEN=secret_your_token_here
NOTION_DATABASE_ID=your_database_id_here
NOTION_PARENT_PAGE_ID=your_parent_page_id_here
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

**Important**: Leave `WEBHOOK_SECRET` empty for now. We'll add it in Step 5.

### Get Your Webhook URL

After deployment completes, Render will provide a URL like:

```
https://notion-automation-xxxx.onrender.com
```

Your webhook endpoint will be:

```
https://notion-automation-xxxx.onrender.com/webhook
```

**⚠️ Important Note about Free Tier:**

- The free tier **sleeps after 15 minutes of inactivity**
- First webhook after sleep will take **30-60 seconds** to wake up
- This is perfectly fine for transcript processing!
- If you need instant response, upgrade to $7/month paid tier

## Step 4: Set Up Notion Webhook

1. Go to https://www.notion.so/my-integrations

2. Click on your integration (from Step 1)

3. Navigate to the **"Webhooks"** tab

4. Click **"+ Create a subscription"**

5. Enter your webhook URL:

   ```
   https://your-app-name.onrender.com/webhook
   ```

6. Select these event types:

   - ✅ `page.created`
   - ✅ `page.content_updated`

7. Click **"Create subscription"**

## Step 5: Verify Your Webhook

1. **Check your Render logs** (in the Render dashboard, click "Logs"):

   ```
   🔐 Received verification token
   Token: secret_xxxYOUR_ACTUAL_TOKEN_WILL_APPEAR_HERExxx
   ⚠️  Copy this token to your Notion webhook settings to complete verification!
   ```

2. **Copy the verification token** from the logs

3. Go back to Notion webhooks tab and click **"⚠️ Verify"**

4. Paste the token and click **"Verify subscription"**

5. **Add the token to Render environment variables:**

   - Go to your Render service → Environment
   - Add new variable:
     ```
     WEBHOOK_SECRET=secret_xxxYOUR_TOKEN_FROM_STEP_1xxx
     ```
   - This enables signature validation for security

6. Your webhook is now **active** ✅

## Step 6: Test with a Sample Transcript

1. Go to your "Raw Transcripts" database in Notion

2. Create a new entry with text in the "Transcript" property:

```
I need to finish the quarterly report by Friday.
First, I should compile the sales data from Q3.
Then analyze the customer feedback survey results.
Finally, create the executive summary presentation.
Also need to schedule a review meeting with the team.
```

3. **Within 1-2 minutes** (or 30-60 seconds if free tier was sleeping), your transcript will be processed!

4. Check your parent page - you should see a new child page created with:
   - Title: Current day and date (e.g., "Monday [10/28/25]")
   - Summary section
   - Task checklist

## Expected Output

In your Render logs, you'll see:

```
📨 Received webhook event: page.created
✓ Event is from target database, processing...
📝 Processing page: abc123...
✓ Found transcript (247 chars)
🤖 Sending to Claude API...
📄 Creating Notion page...
✅ Created page: Monday [10/28/25]
🔗 URL: https://notion.so/...
```

## Troubleshooting

### Webhook Not Receiving Events

**Check Render logs for errors**

- Go to Render dashboard → Your service → Logs
- Look for any error messages

**Webhook subscription not active**

- Verify your webhook is active in Notion integration settings
- Status should show ✅ Active, not ⚠️ Pending

**Integration doesn't have access**

- Go to your database in Notion
- Click "..." → Connections
- Ensure your integration is connected

### Events Received But Not Processing

**"No transcript text found"**

- Ensure your database has a property named exactly **"Transcript"**
- The property should be type "Text" or "Rich Text"
- Verify the property contains actual text

**"Authentication failed"**

- Double-check your `NOTION_TOKEN` environment variable in Render
- Ensure the integration has access to both the database AND parent page

**Claude API errors**

- Verify your `ANTHROPIC_API_KEY` is valid
- Check you have available credits at https://console.anthropic.com/

### Slow Response (30-60 seconds)

This is **normal on the free tier** when the service has been sleeping. Options:

1. **Accept the delay** — it's fine for transcript processing
2. **Upgrade to paid tier** ($7/month) for always-on, instant response

### Invalid Signature Errors

- Make sure you added the `WEBHOOK_SECRET` to Render environment variables
- The secret should match the `verification_token` from Step 5
- If you recreate the webhook, you'll get a new token

## 💰 Cost Summary

### Free Tier (Recommended for Most Users)

- **Render Hosting**: $0/month
  - 750 hours/month (24/7 coverage)
  - 100GB bandwidth
  - Sleeps after 15 min inactivity (30-60s wake time)
- **Anthropic API**: ~$0.003 per transcript

  - Example: 100 transcripts/month ≈ $0.30
  - Example: 1000 transcripts/month ≈ $3.00

- **Notion API**: Free ✅

**Total for 100 transcripts/month: ~$0.30** 🎉

### Paid Option (If You Need Instant Response)

- **Render Hosting**: $7/month (no sleep, instant response)
- **Anthropic API**: Same as above
- **Total**: ~$7-10/month

### Hidden Costs?

❌ **No surprises!** The only variable cost is Claude API usage, which is transparent and based on transcript length.

## Testing Locally (Development Only)

If you want to test locally before deploying:

1. Install dependencies:

```bash
uv sync
```

2. Create `.env` file (copy from `env.example`):

```bash
cp env.example .env
# Edit .env with your credentials
```

3. Run the server:

```bash
uv run python webhook_server.py
```

4. Use **ngrok** to create a public URL:

```bash
ngrok http 8000
```

5. Use the ngrok URL for your Notion webhook

**Note**: This is only for testing. For production, deploy to Render.

## Monitoring Your Service

### View Logs

- Go to Render dashboard
- Click on your service
- Click "Logs" tab
- You'll see real-time webhook events and processing

### Health Check

Visit your service URL to check health:

```
https://your-app-name.onrender.com/health
```

You'll see:

```json
{
	"status": "healthy",
	"notion_configured": true,
	"claude_configured": true,
	"webhook_secret_configured": true,
	"parent_page_configured": true,
	"database_configured": true
}
```

## Updating Your Deployment

Render automatically redeploys when you push to your connected Git repository:

1. Make changes to your code
2. Commit and push to GitHub

```bash
git add .
git commit -m "Update webhook handler"
git push
```

3. Render automatically detects and deploys the changes
4. Check the "Events" tab in Render to track deployment progress

## Advanced: Multiple Databases

To process transcripts from multiple databases:

1. Create separate webhook subscriptions in Notion for each database
2. Update `webhook_server.py` to handle multiple database IDs
3. Add database-specific logic in the event handler

Enjoy your automated, real-time Notion workflow! 🚀
