import json
import random
from datetime import datetime

GAMES_DB = {
    "1": {"id": "1", "name": "Snake Arena",   "players": 0, "max_players": 100, "status": "active"},
    "2": {"id": "2", "name": "Pixel Racer",   "players": 0, "max_players": 50,  "status": "active"},
    "3": {"id": "3", "name": "Tower Defense", "players": 0, "max_players": 200, "status": "maintenance"},
}


def lambda_handler(event, context):
    http_method  = event.get("httpMethod", "GET")
    path_params  = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}
    body         = json.loads(event.get("body") or "{}")
    game_id      = path_params.get("id") or query_params.get("id") or body.get("id")

    if http_method == "GET":
        if game_id:
            game = GAMES_DB.get(game_id)
            if not game:
                return _response(404, {"error": f"Game {game_id} not found"})
            return _response(200, {"status": "success", "game": game})
        return _response(200, {
            "status":     "success",
            "games":      list(GAMES_DB.values()),
            "total":      len(GAMES_DB),
            "active":     sum(1 for g in GAMES_DB.values() if g["status"] == "active"),
            "timestamp":  datetime.utcnow().isoformat(),
        })

    elif http_method == "POST":
        action = body.get("action")
        if action == "join":
            game = GAMES_DB.get(game_id)
            if not game:
                return _response(404, {"error": "Game not found"})
            if game["players"] >= game["max_players"]:
                return _response(409, {"error": "Game is full"})
            session_id = f"session_{random.randint(10000, 99999)}"
            return _response(200, {
                "status":     "joined",
                "game_id":    game_id,
                "session_id": session_id,
                "joined_at":  datetime.utcnow().isoformat(),
            })
        name = body.get("name")
        if not name:
            return _response(400, {"error": "name is required"})
        new_id   = str(len(GAMES_DB) + 1)
        new_game = {
            "id":          new_id,
            "name":        name,
            "players":     0,
            "max_players": body.get("max_players", 100),
            "status":      "active",
            "created_at":  datetime.utcnow().isoformat(),
        }
        return _response(201, {"status": "created", "game": new_game})

    elif http_method == "PUT":
        if not game_id:
            return _response(400, {"error": "Game ID is required"})
        game = GAMES_DB.get(game_id)
        if not game:
            return _response(404, {"error": f"Game {game_id} not found"})
        updated = {**game, **{k: v for k, v in body.items() if k != "id"},
                   "updated_at": datetime.utcnow().isoformat()}
        return _response(200, {"status": "updated", "game": updated})

    elif http_method == "DELETE":
        if not game_id:
            return _response(400, {"error": "Game ID is required"})
        if game_id not in GAMES_DB:
            return _response(404, {"error": f"Game {game_id} not found"})
        return _response(200, {"status": "deleted", "game_id": game_id})

    return _response(405, {"error": "Method not allowed"})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
            "X-Service":                   "game-service",
            "X-Version":                   "1.0.0",
        },
        "body": json.dumps(body),
    }
