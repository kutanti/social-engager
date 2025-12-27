"""Azure Function App for Social Engager.

This module provides HTTP and Timer triggers for the Social Engager agent.
"""

import asyncio
import json
import logging
import os

import azure.functions as func
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = func.FunctionApp()


async def run_social_engager_async() -> dict:
    """Run the social engager workflow asynchronously."""
    from social_engager.graph import run_social_engager

    return await run_social_engager()


def run_social_engager_sync() -> dict:
    """Run the social engager workflow synchronously for Azure Functions."""
    return asyncio.run(run_social_engager_async())


@app.timer_trigger(
    schedule="0 0 9 * * *",  # Run daily at 9 AM UTC
    arg_name="timer",
    run_on_startup=False,
)
def daily_tweet_timer(timer: func.TimerRequest) -> None:
    """Timer trigger to run the social engager daily.

    Cron expression: 0 0 9 * * * = Every day at 9:00 AM UTC
    """
    logging.info("Daily tweet timer triggered")

    if timer.past_due:
        logging.warning("Timer is past due!")

    try:
        result = run_social_engager_sync()

        logging.info("Workflow completed successfully")
        logging.info(f"Topic: {result.get('selected_topic', 'N/A')}")
        logging.info(f"Posted: {result.get('is_posted', False)}")
        logging.info(f"Tweet: {result.get('generated_tweet', 'N/A')[:100]}...")

    except Exception as e:
        logging.error(f"Error running social engager: {e}")
        raise


@app.function_name("RunSocialEngager")
@app.route(route="run", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def run_manual_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger to manually run the social engager.

    POST /api/run
    Optional body: {"dry_run": true/false}
    """
    logging.info("Manual trigger received")

    try:
        # Check for dry_run override in request body
        try:
            body = req.get_json()
            if body and "dry_run" in body:
                os.environ["DRY_RUN"] = str(body["dry_run"]).lower()
        except ValueError:
            pass  # No JSON body

        result = run_social_engager_sync()

        response_data = {
            "success": True,
            "topic": result.get("selected_topic", ""),
            "category": result.get("topic_category", ""),
            "tweet": result.get("generated_tweet", ""),
            "posted": result.get("is_posted", False),
            "post_result": result.get("post_result", ""),
            "tweet_id": result.get("tweet_id", ""),
        }

        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            json.dumps({"success": False, "error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name("HealthCheck")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "social-engager"}),
        status_code=200,
        mimetype="application/json",
    )



