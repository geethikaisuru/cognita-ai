import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer

# Define the local path where the model is stored
local_model_path = "E:/Dev/DevTools/Huggingface/models/openbmb_MiniCPM-Llama3-V-2_5"

# Load the model and tokenizer from the local path
model = AutoModel.from_pretrained(local_model_path, trust_remote_code=True, torch_dtype=torch.float16)
model = model.to(device='cuda')  # Move the model to GPU

tokenizer = AutoTokenizer.from_pretrained(local_model_path, trust_remote_code=True)
model.eval()

def ask_question(question, image_path=None):
    msgs = [{'role': 'user', 'content': question}]
    image = None

    if image_path:
        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            print(f"Error loading image: {e}")
            return "Error: Unable to load the image."

    res = model.chat(
        image=image,
        msgs=msgs,
        tokenizer=tokenizer,
        sampling=True,
        temperature=0.7,
    )
    return res

def ask_question_stream(question, image_path=None):
    msgs = [{'role': 'user', 'content': question}]
    image = None

    if image_path:
        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            print(f"Error loading image: {e}")
            return "Error: Unable to load the image."

    res = model.chat(
        image=image,
        msgs=msgs,
        tokenizer=tokenizer,
        sampling=True,
        temperature=0.7,
        stream=True
    )

    generated_text = ""
    for new_text in res:
        generated_text += new_text
        print(new_text, flush=True, end='')
    
    return generated_text

# Example usage
question = "What is the capital of France?"

# Non-streaming version
answer = ask_question(question)
print(f"\nAnswer: {answer}")

# Streaming version
print("\nStreaming answer:")
streaming_answer = ask_question_stream(question)
print(f"\nFull streaming answer: {streaming_answer}")

# If you want to use an image, uncomment the following lines and provide the image path
# image_path = 'path/to/your/image.jpg'
# image_question = "What is in the image?"
# image_answer = ask_question(image_question, image_path)
# print(f"\nImage Answer: {image_answer}")