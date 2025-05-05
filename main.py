import json
import os

from camel.agents import ChatAgent
from camel.embeddings import OpenAIEmbedding
from camel.messages import BaseMessage
from camel.retrievers import VectorRetriever
from camel.storages import QdrantStorage
from camel.types import OpenAIBackendRole

class RolePlayBot:
    def __init__(self):
        self.sheldon = ChatAgent(
            system_message="You are Dr. Sheldon Cooper from *The Big Bang Theory*. "
                           "You respond with intellectual superiority, sarcasm, and a direct, declarative tone. "
                           "You belittle engineering, geology, and MIT whenever relevant. "
                           "You never give long-winded explanations—your responses are concise, cutting, and brutally logical. "
                           "Do not use softening language or rhetorical introductions. No 'Ah,' no 'Well.' Start with the fact. "
                           "You don't ask questions unless correcting a logical or scientific fallacy. "
                           "You must be addressed as 'Dr. Sheldon Cooper'."
        )
        # self.read_from_long_term_memory()
        self.scene_storage = QdrantStorage(
            vector_dim=OpenAIEmbedding().get_output_dim(),
            collection_name="classic_scenes",
            path="./scene_vector_db",
        )
        self.game_interaction_storage = QdrantStorage(
            vector_dim=OpenAIEmbedding().get_output_dim(),
            collection_name="game_interaction",
            path="./interaction_vector_db",
        )
        self.scene_retriever = self.init_scenes(self.scene_storage)
        self.game_interaction_retriever = VectorRetriever(
            embedding_model=OpenAIEmbedding(),
            storage=self.game_interaction_storage
        )

    def read_from_long_term_memory(self):
        with open("sheldon_persona.json", "r", encoding="utf-8") as file:
            char_persona = json.load(file)
            persona_content = json.dumps(char_persona, indent=2)
            long_term = BaseMessage.make_assistant_message(
                role_name="Assistant",
                content=persona_content,
            )
            self.sheldon.update_memory(long_term, OpenAIBackendRole.SYSTEM)

    def summarize(self):
        summary_prompt = (
            "Please summarize the conversation so far focusing on key "
            "events, decisions, and character traits. Keep it to "
            "three concise sentences."
        )
        summary = self.sheldon.step(summary_prompt).msgs[0].content
        return summary

    def init_scenes(self, scene_storage) -> VectorRetriever:
        vr = VectorRetriever(
            embedding_model=OpenAIEmbedding(),
            storage=scene_storage
        )

        # self.load_scenes_from_directory(vr=vr)
        return vr

    def load_scenes_from_directory(
        self,
        vr: VectorRetriever,
        directory: str = "./scenes"
    ):
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                file_path = os.path.join(directory, filename)
                vr.process(
                    content=file_path,
                    metadata_filename=filename
                )

    def load_pending_interactions(self):
        dir_path = "./pending_interactions"
        if not os.path.exists(dir_path):
            return

        for filename in os.listdir(dir_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(dir_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                        if text:
                            self.add_interaction(text)
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to process {filename}: {e}")

    def add_interaction(
        self,
        text: str,
    ):
        self.game_interaction_retriever.process(
            content=text
        )

    def preprocess_retrieved_scenes(
        self,
        query: str,
    ) -> str:
        retrieved_scenes = self.scene_retriever.query(
            query,
            similarity_threshold=0.1,
            top_k=5,
        )
        scene_texts = "\n\n".join(
            [scene["text"] for scene in retrieved_scenes])
        filter_prompt = (f"The player is asking {query}, and we retrieved some "
                         f"past interaction scenes:\n\n{scene_texts}, please "
                         f"only reply with the scene texts that's related to the "
                         f"player query, don't add anything else. If it's all "
                         f"unrelated, only reply NO.")
        if filter_prompt == "NO":
            prompt = query
        else:
            prompt = (
                "Here are some classic scenes retrieved for Sheldon to "
                "reference:\n\n"
                f"{scene_texts}\n\n"
                "Now based on the above context, please respond as Sheldon "
                "would: "
                f"\n\n{query}"
            )
        return prompt

    def pre_process_retrieved_game_interaction(
        self,
        query: str,
    ) -> str:
        self.load_pending_interactions()
        try:
            retrieved_interactions = self.game_interaction_retriever.query(
                query,
                similarity_threshold=0,
                top_k=5,
            )
        except Exception as e:
            return ""
        interaction_texts = "\n\n".join(
            [interaction["text"] for interaction in retrieved_interactions]
        )
        filter_prompt = (f"The player is asking {query}, and we retrieved some "
                         f"past interaction scenes:\n\n{interaction_texts}, please "
                         f"only reply with the scene texts that's related to the "
                         f"player query, don't add anything else. If it's all "
                         f"unrelated, only reply NO.")
        if filter_prompt == "NO":
            return ""
        else:
            prompt = (
                "Here are some past interaction retrieved for Sheldon to "
                "reference:\n\n"
                f"{interaction_texts}\n\n"
                "Now based on the above context, please respond as Sheldon "
                "would (disregard if the interaction is unrelated): "
                f"\n\n{query}"
            )
        return prompt

    def get_response(
        self,
        query: str,
    ) -> str:
        prompt = self.preprocess_retrieved_scenes(query)
        interaction = self.pre_process_retrieved_game_interaction(query)
        if interaction:
            prompt += "\n\n" + interaction
        return self.sheldon.step(prompt).msgs[0].content

bot = RolePlayBot()

if __name__ == "__main__":
    turn_count = 0
    summary_interval = 10
    while True:
        player_input = input("You: ")
        if player_input.lower() in ["exit", "quit"]:
            break
        response = bot.get_response(player_input)
        print(f"Sheldon: {response}")
        turn_count += 2

        if turn_count >= summary_interval:
            summary = bot.summarize()
            print("\n--- Conversation Summary ---")
            print(summary)
            print("----------------------------\n")
            bot.sheldon.reset()

            bot.sheldon.update_memory(
                BaseMessage.make_assistant_message(
                    role_name="Assistant",
                    content=summary,
                ),
                OpenAIBackendRole.SYSTEM
            )

            turn_count = 0
