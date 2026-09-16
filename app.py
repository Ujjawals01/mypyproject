from fastapi import FastAPI, WebSocket
import chess
import uuid

app = FastAPI(title="Advanced Chess API")

games = {}


@app.post("/game")
def create_game():
    game_id = str(uuid.uuid4())

    games[game_id] = {
        "board": chess.Board(),
        "moves": []
    }

    return {
        "game_id": game_id,
        "fen": games[game_id]["board"].fen()
    }


@app.get("/game/{game_id}")
def get_game(game_id: str):
    game = games[game_id]

    return {
        "fen": game["board"].fen(),
        "moves": game["moves"],
        "turn": "white" if game["board"].turn else "black",
        "check": game["board"].is_check(),
        "checkmate": game["board"].is_checkmate(),
        "stalemate": game["board"].is_stalemate()
    }


@app.post("/game/{game_id}/move")
def make_move(game_id: str, move: str):
    game = games[game_id]
    board = game["board"]

    chess_move = chess.Move.from_uci(move)

    if chess_move not in board.legal_moves:
        return {
            "success": False,
            "error": "Illegal move"
        }

    san = board.san(chess_move)
    board.push(chess_move)

    game["moves"].append({
        "uci": move,
        "san": san
    })

    return {
        "success": True,
        "move": san,
        "fen": board.fen(),
        "check": board.is_check(),
        "checkmate": board.is_checkmate()
    }


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str
):
    await websocket.accept()

    while True:
        data = await websocket.receive_json()

        move = data["move"]

        game = games[game_id]
        board = game["board"]

        chess_move = chess.Move.from_uci(move)

        if chess_move in board.legal_moves:
            san = board.san(chess_move)
            board.push(chess_move)

            await websocket.send_json({
                "move": san,
                "fen": board.fen(),
                "check": board.is_check(),
                "checkmate": board.is_checkmate()
            })
