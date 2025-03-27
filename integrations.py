import os
from brainbase_labs import BrainbaseLabs
from dotenv import load_dotenv
from openai import OpenAI
import base64
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship


# Load environment variables from .env file
load_dotenv()

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_brainbase_client():
    # Access environment variables
    BRAINBASE_API_KEY = os.getenv('BRAINBASE_API_KEY')
    client = BrainbaseLabs(
        api_key=BRAINBASE_API_KEY,  # This is the default and can be omitted
    )
    return client

def get_openai_client():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    return client

def read_text_in_image(image_path: str):
    # Getting the Base64 string
    client = get_openai_client()
    base64_image = encode_image(image_path)

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    { "type": "text", "text": "Return only the text that is in the image. Be as precise." },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
    )
    return completion.choices[0].message.content

def pdf2image(pdf_path: str):
    from pdf2image import convert_from_path
    images = convert_from_path(pdf_path)
    images_path = pdf_path[:-len(".pdf")].replace(" ", "_")
    os.mkdir(images_path)

    # Save each page as an image
    for i, image in enumerate(images):
        image.save(f"{images_path}/page_{i + 1}.png", "PNG")

    return images_path

if __name__ == "__main__":
    # print(read_text_in_image("data/a1.png"))
    # pdf2image("data/Anchor - 2b.pdf")
    # print(read_text_in_image("data/Anchor_-_2b/page_1.png"))
    example_text = {
        "filepath": "data/Anchor_-_2b/page_1.png", "text": """Puerto Rico

I visited puerto rico in 2015
Summer there are some of the n thing puerto Rico 
It was very hipical Also it had lots of 
trees. Next had very warn, water the water 
color was lightish blue and it was at the 
ocean. Therefor, Puerto Rico had very good 
food my faverit food for now was 
the bear sauce and chicken at Puerto rico 
in a resterunt it smelled very good.
The people there were hat diffrent 
Finally, the worst part was that I steped 
on a dead sea urchin also the wether was 
very hot. 

At the hotel we stayed at a 
place there was a pool and I
really liked to go into the pool 
in the night and day. We also got some 
thing that you dive for."""
    }
