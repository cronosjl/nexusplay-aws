import json
from datetime import datetime

USERS_DB = {
    "1": {"id": "1", "username": "player1", "email": "player1@nexusplay.io", "score": 1500, "level": 10},
    "2": {"id": "2", "username": "player2", "email": "player2@nexusplay.io", "score": 2300, "level": 15},
    "3": {"id": "3", "username": "admin",   "email": "admin@nexusplay.io",   "score": 9999, "level": 99},
}


def lambda_handler(event, context):
    http_method  = event.get("httpMethod", "GET")
    path_params  = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}
    body         = json.loads(event.get("body") or "{}")
    user_id      = path_params.get("id") or query_params.get("id") or body.get("id")

    if http_method == "GET":
        if user_id:
            user = USERS_DB.get(user_id)
            if not user:
                return _response(404, {"error": f"User {user_id} not found"})
            return _response(200, {"status": "success", "user": user})
        leaderboard = sorted(USERS_DB.values(), key=lambda u: u["score"], reverse=True)
        return _response(200, {
            "status":      "success",
            "users":       leaderboard,
            "total":       len(USERS_DB),
            "timestamp":   datetime.utcnow().isoformat(),
        })

    elif http_method == "POST":
        username = body.get("username")
        email    = body.get("email")
        if not username or not email:
            return _response(400, {"error": "username and email are required"})
        new_id   = str(len(USERS_DB) + 1)
        new_user = {
            "id":         new_id,
            "username":   username,
            "email":      email,
            "score":      0,
            "level":      1,
            "created_at": datetime.utcnow().isoformat(),
        }
        return _response(201, {"status": "created", "user": new_user})

    elif http_method == "PUT":
        if not user_id:
            return _response(400, {"error": "User ID is required"})
        user = USERS_DB.get(user_id)
        if not user:
            return _response(404, {"error": f"User {user_id} not found"})
        updated = {**user, **{k: v for k, v in body.items() if k != "id"},
                   "updated_at": datetime.utcnow().isoformat()}
        return _response(200, {"status": "updated", "user": updated})

    elif http_method == "DELETE":
        if not user_id:
            return _response(400, {"error": "User ID is required"})
        if user_id not in USERS_DB:
            return _response(404, {"error": f"User {user_id} not found"})
        return _response(200, {"status": "deleted", "user_id": user_id})

    return _response(405, {"error": "Method not allowed"})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
            "X-Service":                   "user-service",
            "X-Version":                   "1.0.0",
        },
        "body": json.dumps(body),
    }
