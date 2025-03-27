# from llama_index import ServiceContext, LLMPredictor
from openai import OpenAI
import json
import os
from dotenv import load_dotenv


load_dotenv()

prompt_one_grader = """You are an expert writing evaluator and you are going to write evaluations for children between the age of 5 and 12. Given the essay below, assess it based on the following categories:
Ideas:
Are the ideas clear, focused, and original?
Grade (1-5): Provide detailed reasoning.

Organization:
Are the ideas organized effectively with clear transitions?
Grade (1-5): Provide detailed reasoning.

Voice:
Does the writing clearly express the writer's personality, perspective, and engage the reader?
Grade (1-5): Provide detailed reasoning.

Word Choice:
Does the writer use precise, vivid, and varied vocabulary effectively, including figurative language?
Grade (1-5): Provide detailed reasoning.

Sentence Fluency:
Are sentences well-structured with rhythmic, varied flow?
Grade (1-5): Provide detailed reasoning.

Conventions:
Is the essay free from spelling, punctuation, and grammatical errors?
Grade (1-5): Provide detailed reasoning.

After providing grades, include specific, actionable suggestions for improvement in each category.

Essay:"""

prompt_ideas = """ Ideas Grader: You are an expert writing evaluator and you are going to write evaluations for children between the age of 5 and 12. Given the essay below, evaluate the essay specifically for the clarity, originality, and development of ideas. Grade (1-5) based on how clear, focused, original, and thoroughly developed the main idea is. Provide detailed reasoning and succint suggestions (less than 180 characters) for improving idea development and creativity.
Grades explanation:
1: I started my writing, but I need to add ideas connected to the topic.
2: I have a focus, but I need to make my main idea clearer.
3: I have a generally clear, focused, and accurate main idea, but I need to share creative ideas.
4: I have a clear, focused, and fully developed main idea, but can share my own thoughts and opinions more creatively.
5: I have a clear, focused, important, and fully developed main idea, with original thoughts and opinions.
"""

prompt_organization = """ Organization Grader: You are an expert writing evaluator and you are going to write evaluations for children between the age of 5 and 12. Given the essay below, evaluate the essay specifically for organization, structure, clarity of transitions, and effectiveness of the conclusion. Grade (1-5) based on how well-organized, clear, and purposeful the writing is. Provide detailed reasoning and succint suggestions (less than 180 characters)  for improving the essay's organization and transitions.
Grades explanation:
1: I have sentences, but I can organize them better so they make more sense.
2: I have sentences but I need to organize my ideas into a clear paragraph and add transitions.
3: I have sentences that make sense together, but I need to cover the main ideas clearly in paragraphs with purposeful transitions.
4: I have a clear purpose throughout my writing and use transitions to connect different ideas, but my writing needs more variety. My ideas are separated into different paragraphs.
5: I have a clear purpose, satisfying conclusion, and use thoughtful, varied language to keep the reader's attention.
"""

prompt_voice = """ Voice Grader: You are an expert writing evaluator and you are going to write evaluations for children between the age of 5 and 12. Given the essay below, evaluate the essay specifically for voice, tone, expression of personality, and reader engagement. Grade (1-5) based on how effectively the writer expresses their opinion, engages the reader, and shows personality in the writing. Provide detailed reasoning and succint suggestions (less than 180 characters)  for improving the essay's voice and reader engagement.
Grades explanation:
1: I have sentences, but I need to express my opinion.
2: I shared my opinion, but I can express how I feel about the topic better.
3: I have shown some of my personality and opinions, but I need to add more flavor and hook the reader more.
4: I use a tone that supports my topic and engages my reader, but my writing needs to explore my perspective more and consider the audience.
5: I have a strong tone that supports my topic and engages the reader, and I consistently use a variety of techniques to enhance the flavor of my writing.
"""

prompt_word_choice = """ Word Choice Grader: You are an expert writing evaluator and you are going to write evaluations for children between the age of 5 and 12. Given the essay below, evaluate the essay specifically for word choice, vocabulary variety, and use of figurative language. Grade (1-5) based on how well the writer selects words to enhance meaning and avoid repetition. Provide detailed reasoning and succint suggestions (less than 180 characters)  for improving word choice and vocabulary usage.
Grades explanation:
1: I have ideas, but I need to make sure I use the right words without repeating.
2: I have some juicy words, but I can add more juicy words that fit.
3: I have juicy vocabulary that makes sense, but I can include some figurative language.
4: I use a variety of vocabulary, but I can choose more specific words and figurative language to create an image in my reader’s mind.
5: I use strong and specific words to create imagery for my reader, but I can add more powerful/varied types of figurative language.
"""

prompt_sentence_fluency = """ Sentence Fluency Grader: You are an expert writing evaluator and you are going to write evaluations for children between the age of 5 and 12. Given the essay below, evaluate the essay specifically for sentence structure, rhythm, and variety. Grade (1-5) based on how well the sentences flow, their complexity, and variation in structure. Provide detailed reasoning and succint suggestions (less than 180 characters)  for improving sentence fluency and rhythm.
Grades explanation:
1: I have complete sentences, but they can be reorganized to help my reader understand them better.
2: I have sentences that make sense, but I can try using complex and compound sentences.
3: I have a variety of sentence beginnings, but I can create more variety in my sentence types for more flow and rhythm.
4: I have sentences with rhythm and my ideas flow well between one and the next, but I could use more complex sentences to move the piece forward.
5: I have well-structured sentences with strong rhythm and cadence, and I use varied words/phrases to enhance the flow of the overall writing.
"""

prompt_conventions = """ Conventions Grader: You are an expert writing evaluator and you are going to write evaluations for children between the age of 5 and 12. Given the essay below, evaluate the essay specifically for spelling, punctuation, and grammar accuracy. Grade (1-5) based on how well the writer follows standard writing conventions. Provide detailed reasoning and succint suggestions (less than 180 characters) for improving grammar, punctuation, and spelling.
Grades explanation:
1: I have ideas, but I need to add periods and capital letters.
2: I have sentences and the reader understands some of what I’m saying, but I have some errors that make my writing hard to understand.
3: My sentences make sense. I have mostly used correct spelling and punctuation, but there are minor errors.
4: I consistently use correct spelling, punctuation, and grammar, but could introduce a variety of punctuation.
5: My writing is error-free and my choices in punctuation and grammar contribute to the creativity and clarity of the piece.
"""


def single_grader(essay_text: str, prompt: str =prompt_one_grader):
    """
    Grades an essay using LlamaIndex with OpenAI chat models.
    
    Parameters:
    - essay_text (str): The text of the essay to be graded.
    - prompt (str): The grading criteria prompt.

    Returns:
    - dict: A dictionary containing the grade and comments.
    """

    # Initialize LlamaIndex with OpenAI's GPT-4 model
    # service_context = ServiceContext.from_defaults(
    #     llm=OpenAI(model="gpt-4-turbo", temperature=0)
    # )
    # llm_predictor = LLMPredictor(llm=service_context.llm)

    # Use the structured chat format with system and user messages
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Here is the essay to be graded:\n\n{essay_text}\n\nProvide a structured JSON response with 'grade' and 'comments' as keys."}
    ]
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Get the response from LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"},
    )

    try:
        result = json.loads(response.choices[0].message.content)
        return result
    except json.JSONDecodeError:
        return {"error": "Failed to parse LLM response. Try reformatting the prompt."}

def grade_essay(essay: str):
    categories = {
        "ideas": prompt_ideas,
        "organization": prompt_organization,
        "voice": prompt_voice,
        "word_choice": prompt_word_choice,
        "sentence_fluency": prompt_sentence_fluency,
        "conventions": prompt_conventions,
    }
    graders = []
    for category, prompt in categories.items():
        result = single_grader(essay, prompt=prompt)
        graders.append({
            "type": category,
            "grade": result.get("grade", "N/A"),
            "comments": result.get("comments", "N/A")
        })
    return graders

if __name__ == "__main__":
    essay_example = "This is an example essay. It should be evaluated based on the given rubric."
    print(grade_essay(essay_example))