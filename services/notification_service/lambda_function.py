import json
import boto3
import os
from datetime import datetime

sns_client = boto3.client("sns", region_name="us-east-1")


def lambda_handler(event, context):
    http_method = event.get("httpMethod", "POST")
    body        = json.loads(event.get("body") or "{}")

    if http_method == "POST":
        notif_type = body.get("type", "info")
        message    = body.get("message", "")
        subject    = body.get("subject", "NexusPlay Notification")

        if not message:
            return _response(400, {"error": "message is required"})

        topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
        result    = {"type": notif_type, "message": message, "sent_at": datetime.utcnow().isoformat()}

        if topic_arn:
            try:
                sns_client.publish(
                    TopicArn=topic_arn,
                    Message=json.dumps({
                        "type":    notif_type,
                        "message": message,
                        "time":    datetime.utcnow().isoformat(),
                    }),
                    Subject=subject,
                )
                result["sns_status"] = "sent"
            except Exception as e:
                result["sns_status"] = f"failed: {str(e)}"
        else:
            result["sns_status"] = "no_topic_configured"

        return _response(200, {"status": "success", "notification": result})

    elif http_method == "GET":
        return _response(200, {
            "status":  "healthy",
            "service": "notification-service",
            "time":    datetime.utcnow().isoformat(),
        })

    return _response(405, {"error": "Method not allowed"})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
            "X-Service":                   "notification-service",
        },
        "body": json.dumps(body),
    }
