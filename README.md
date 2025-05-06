# RolePlayBot

**RolePlayBot** is a conversational bot built to emulate Dr. Sheldon Cooper from *The Big Bang Theory*. It supports interactive dialogues and integrates with a visual novel-style game to remember player-specific interactions over time.

## Repos

- **Bot logic and server**: [RolePlayBot](https://github.com/AveryYay/RolePlayBot)
- **Visual novel game frontend**: [RolePlayBot_VisualNovel](https://github.com/AveryYay/RolePlayBot_VisualNovel)

## Project Structure

- `main.py`: CLI entry point to talk with the bot directly.
- `server.py`: Hosts an endpoint (`/add_interaction`) that the game calls to sync data.
- `interaction_vector_db/`: Stores long-term player-specific interactions.
- `scene_vector_db/`: Stores embedded classic scenes to ground Sheldon's persona.
- `scenes/`: Raw `.txt` files used to populate `scene_vector_db`.
- `sheldon_persona.json`: Optional persona definition for additional system messages.

## How It Works

1. **Scene Preparation**  
   Classic scenes are collected from the show (and optionally other sources) and saved as `.txt` files. These are embedded using OpenAI embeddings and stored in `scene_vector_db`.

2. **Game Integration**  
   After a game session, the player can click a **sync** button. This sends a POST request to `/add_interaction` with the latest game log. The server summarizes the scene and stores it in `interaction_vector_db`.

3. **Dialogue Memory**  
   The bot retrieves from both memory banks:
   - **Scene memory** provides Sheldon's voice and style.
   - **Interaction memory** ensures continuity across game sessions.

4. **Short-Term and Long-Term Memory**  
   The bot clears short-term memory every 10 dialogue turns and summarizes the interaction, appending it to the long-term memory database.

## Run Locally

```bash
# Start the bot
python main.py

# Or start the server
python server.py
```

Game syncs automatically by calling the `/add_interaction` endpoint exposed by `server.py`.

## Notes

This project takes inspiration from [ChatHaruhi's architecture](https://github.com/yizhongw/ChatHaruhi), adapted to focus on a highly distinctive character with both scripted and dynamic memory.
