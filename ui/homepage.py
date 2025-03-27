import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import warnings
import time
from wordcloud import WordCloud
# import nltk
import requests
# from nltk.tokenize import word_tokenize
# from nltk.corpus import stopwords
from collections import Counter
import matplotlib.pyplot as plt
db_to_nice_str_map = {
    "ideas": "Ideas",
    "organization": "Organization",
    "voice": "Voice",
    "word_choice": "Word Choice",
    "sentence_fluency": "Sentence Fluency",
    "conventions": "Conventions"
}
ordered_types = ["ideas", "organization", "voice", "word_choice", "sentence_fluency", "conventions"]

warnings.filterwarnings("ignore")
API_URL = "http://127.0.0.1:8000"

@st.cache_data
def fetch_evaluation_results(authorname, essay_title, uploaded_files):
    """Caches API call results to prevent redundant requests."""
    files = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]

    response = requests.post(
        f"{API_URL}/submit-essay/?authorname={authorname}&title={essay_title}",
        files=files
    )

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.json().get("detail", "Unknown error")}


# Setting the title and page icon
st.set_page_config(
    page_title="Evaluator", page_icon=":material/grading:", layout="wide"
)

def fetch_authors():
    """Fetches authors from the FastAPI backend."""
    response = requests.get(f"{API_URL}/get-authors/")
    if response.status_code == 200:
        return response.json()["authors"]
    else:
        st.error(f"Error fetching authors: {response.json().get('detail', 'Unknown error')}")
        return []

def fetch_author_essays(authorname):
    """Fetches essays and grades for a specific author from FastAPI."""
    response = requests.post(f"{API_URL}/get-author-grades/?authorname={authorname}")    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching author essays: {response.json().get('detail', 'Unknown error')}")
        return []


def authors():
    st.title("📚 Author Work")
 
    # Fetch authors
    authors_data = fetch_authors()
    author_names = [author["authorname"] for author in authors_data if author["authorname"]]
 
    if not author_names:
        st.warning("No authors found.")
        return
 
    # Select Author
    selected_author = st.selectbox("👤 Select an Author", author_names)
 
    if not selected_author:
        return
 
    # Fetch essays for selected author
    author_essays = fetch_author_essays(selected_author)
 
    if not author_essays:
        st.warning("No essays found for this author.")
        return
 
    # Extract grade types dynamically
    all_grade_types = [db_to_nice_str_map[e] for e in ordered_types]
    data = []
    for essay in author_essays:
        essay_row = {
            "Title": essay["title"],
            "Date Submitted": essay["date_submitted"],
        }
        for grade_type in all_grade_types:
            essay_row[grade_type] = None  # Initialize all grade columns with None
        for grade in essay["grades"]:
            essay_row[db_to_nice_str_map[grade["type"]]] = grade["grade"]  # Assign the correct grade
        data.append(essay_row)
 
    df = pd.DataFrame(data)
 
    # Display Table with Grades as Columns
    st.subheader(f"📝 {selected_author}'s Work")
    # Remove the index and format the table properly
    styled_table = df.style.format({"Ideas": "{:.0f}", "Organization": "{:.0f}", "Voice": "{:.0f}", "Word Choice": "{:.0f}", "Sentence Fluency": "{:.0f}", "Conventions": "{:.0f}"}).hide(axis="index").to_html()

    # Display table using markdown to fully remove index
    st.markdown(styled_table, unsafe_allow_html=True)
    # st.dataframe(df)

    # **Grouped Bar Plot for Grades**
    st.subheader("📊 Essay Grades Breakdown")
 
    # Transform data for Plotly
    melted_df = df.melt(id_vars=["Title", "Date Submitted"], var_name="Grade Type", value_name="Score")
    melted_df.dropna(inplace=True)  # Remove NaN values
 
    if not melted_df.empty:
        fig = px.bar(melted_df, x="Title", y="Score", color="Grade Type", 
                     barmode="group",
                     labels={"Score": "Grade", "Title": "Essay Title"},
                     height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Prepare essay selection with date in front and sort descending by date
    df["Date Submitted"] = pd.to_datetime(df["Date Submitted"])
    df = df.sort_values(by="Date Submitted", ascending=False)
    df["Title with Date"] = df["Date Submitted"].dt.strftime('%Y-%m-%d') + " - " + df["Title"]

    # **Detailed View of Selected Essay**
    selected_essay_title = st.selectbox("📜 Select an Essay to View Detailed Grades", df["Title with Date"])
 
    if selected_essay_title:
        # Extract the original title (remove the prepended date)
        selected_essay_original_title = selected_essay_title.split(" - ", 1)[1] if " - " in selected_essay_title else selected_essay_title
        selected_essay = next((essay for essay in author_essays if essay["title"] == selected_essay_original_title), None)
 
        if selected_essay:
            st.subheader("🏆 Detailed Essay Grades")
            detailed_data = []
            for grade in selected_essay["grades"]:
                detailed_data.append({
                    "Grade Type": db_to_nice_str_map[grade["type"]],
                    "Score": int(grade["grade"]),
                    "Comments": grade["comments"]
                })
            detailed_df = pd.DataFrame(detailed_data)
            # Remove the index and format the table properly
            styled_table = detailed_df.style.format({"Score": "{:.0f}"}).hide(axis="index").to_html()

            # Display table using markdown to fully remove index
            st.markdown(styled_table, unsafe_allow_html=True)

 
            st.subheader(" ✍️  Full Essay Text")
            # Layout: Display images on the left and text on the right
            cols = st.columns([1, 2])  # Adjust column widths
            DATA_DIR = "test_data/"
            # Display images (if any)
            with cols[0]:
                if selected_essay["images"]:
                    for image_path in selected_essay["images"]:
                        st.image(DATA_DIR + image_path)

            # Display essay text
            with cols[1]:
                st.write(selected_essay["text"])

def home():
    # st.title(":material/grading: Writing Evaluation")
    st.title("🏡 AI Writing Evaluator")
    st.subheader("Welcome to the 826 Valencia AI Writing Evaluator!")

    st.markdown(
        """
        Providing feedback on student writing is essential, but we know it can be time-consuming.
        This tool is designed to help **826 Valencia's staff and volunteers** efficiently assess writing samples while maintaining
        the personal touch that makes mentorship so valuable.

        With AI-powered evaluation, you can:  
        ✅ **Quickly analyze writing samples** based on 826 Valencia's grading rubric.  
        ✅ **Receive high-quality, personalized feedback** tailored to each student's strengths and areas for improvement.  
        ✅ **Save time and focus on mentorship** by reducing the administrative burden of grading.

        **Our goal?** To empower educators and volunteers with a **fast, easy-to-use, and cost-effective**
        solution for evaluating student writing, so you can spend more time inspiring creativity!
        
        - ------------------
        
        ## 📝 How It Works

        ### 1️⃣ Choose Your Upload Method:

        - **File Upload:** Upload a single student writing sample or multiple writing samples(.txt, .docx, .pdf).

        ### 2️⃣ AI-Powered Evaluation:

        - The tool will analyze writing based on 826 Valencia’s grading rubric.
        - It provides **structured scores** and **detailed feedback**, including actionable suggestions for improvement.

        ### 3️⃣ Review & Download Feedback:

        - View the results instantly on the platform.
        - Download feedback reports for individual or bulk submissions.

        ### 4️⃣ Use Feedback for Mentorship:

        - Share AI-generated insights with students.
        - Provide personalized guidance based on AI suggestions.
        """

    )


def writing_evaluation():
    st.title(":material/grading: Writing Evaluator")
    st.subheader(
        "Upload a file to evaluate the writing based on the 826 Valencia Rubric.")
    
    # Capture author name
    author_name = st.text_input("👤 Author Name", "Anonymous")

    # Capture essay title
    essay_title = st.text_input("📝 Essay Title", "Untitled")

    # File uploader for images
    uploaded_files = st.file_uploader(":file_folder: Upload essay images (JPG/PNG)", type=["jpg", "png"], accept_multiple_files=True)

    # TODO: Send files to the backend API
    
    if st.button("🚀 Submit for Evaluation"):
        if not uploaded_files:
            st.warning("Please upload at least one image.")
            return
        
        if not author_name or not essay_title:
            st.warning("Please enter an author name and essay title.")
            return

        st.info("📡 Uploading and processing...")

        result = fetch_evaluation_results(author_name, essay_title, uploaded_files)

        # Display results
        st.success("Evaluation Complete! Here are the results:")
        # Detect Streamlit Theme (Light/Dark Mode)
        theme = st.get_option("theme.base")
        light_mode = theme == "light"

        # Define rubric criteria based on 826 Valencia grading rubric
        
        rubric_criteria = [
            "Ideas", "Organization", "Voice", "Word Choice",
            "Sentence Fluency", "Conventions"
        ]

        # Mock evaluation results (Replace with real backend results)
        new_evaluation_results = {}
        for grade in result["grades"]:
            nice_str_grade_type = db_to_nice_str_map[grade["type"]]
            new_evaluation_results[nice_str_grade_type] = {
                "score": grade["grade"],
                "comment": grade["comments"]
            }
        # evaluation_results = {
        #     db_to_nice_str_map[grade["type"]]: {"score": 5, "comment": "Strong ideas, but needs more supporting details."},
        #     "Organization": {"score": 4, "comment": "Well-structured, logical sequence of thoughts."},
        #     "Voice": {"score": 3, "comment": "Engaging but could be more distinctive."},
        #     "Word Choice": {"score": 2, "comment": "Good vocabulary but some repetitive words."},
        #     "Sentence Fluency": {"score": 3, "comment": "Smooth flow, but some choppy transitions."},
        #     "Conventions": {"score": 2, "comment": "Some grammar and punctuation errors."}
        # }
        evaluation_results = new_evaluation_results
        # Extract comments
        all_comments = " ".join([v["comment"]
                                for v in evaluation_results.values()])

        # Convert data to DataFrame for visualization
        df = pd.DataFrame(
            [(k, v["score"]) for k, v in evaluation_results.items()],
            columns=["Criterion", "Score"]
        )

        with st.expander("📄 View Essay"):
            st.write(result["text"])

        # 📝 Feedback Table
        st.subheader("💡 Feedback & Comments")

        # Apply dark mode or light mode styles dynamically
        table_bg_color = "#f4f4f4" if light_mode else "#333333"
        table_text_color = "#000000" if light_mode else "#f4f4f4"
        border_color = "#dddddd" if light_mode else "#555555"

        comments_html = f"""
        <style>
            table {{ width: 100%; border-collapse: collapse; font-size: 16px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid {border_color}; }}
            th {{ background-color: {table_bg_color}; color: {table_text_color}; }}
            td {{ background-color: transparent; color: {table_bg_color}; }}
        </style>
        <table>
            <tr><th>Criterion</th><th>Score</th><th>Feedback</th></tr>
        """
        for criterion in rubric_criteria:
            score = evaluation_results[criterion]["score"]
            comment = evaluation_results[criterion]["comment"]
            comments_html += f"<tr><td><b>{criterion}</b></td><td>{score}</td><td>{comment}</td></tr>"
        comments_html += "</table>"

        st.markdown(comments_html, unsafe_allow_html=True)

        word_cloud(all_comments, light_mode)
        # 🎨 Bar Chart Visualization
        st.subheader("📊 Writing Evaluation Results")
        fig = px.bar(df, x="Criterion", y="Score", text="Score",
                     color="Score", color_continuous_scale="blues")
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis_range=[0, 5], height=400)
        st.plotly_chart(fig, use_container_width=True)


def word_cloud(all_comments, light_mode):

    # Tokenize words and identify adjectives
    # words = word_tokenize(all_comments)
    # tagged_words = nltk.pos_tag(words)  # POS tagging

    # List of positive adjectives (expandable)
    positive_adjectives = list({
        "strong", "creative", "engaging", "good", "smooth",
        "clear", "logical", "distinctive", "visually", "improving",
        "excellent", "amazing", "fantastic", "brilliant", "creative",
        "engaging", "insightful", "clear", "strong", "persuasive",
        "compelling", "impressive", "remarkable", "eloquent", "thoughtful"
    })

    # Filter adjectives from comments
    # filtered_words = [word for word, tag in tagged_words if tag in (
    #     "JJ", "JJR", "JJS") and word.lower() in positive_adjectives]

    # Generate Word Cloud
    # TODO: Create a list of filtered words
    wordcloud_text = " ".join(positive_adjectives[:5])
    wordcloud = WordCloud(
        width=800, height=400, background_color="white" if light_mode else "white",
        colormap="Blues" if light_mode else "coolwarm"
    ).generate(wordcloud_text)

    # Display Word Cloud
    st.subheader("🌟 Word Cloud")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")  # Hide axes
    st.pyplot(fig)


def about():
    st.title("ℹ️ Rubric")
    # Run function to display rubric
    display_rubric()
    # st.write("This is an app built with Streamlit.")


def contact():
    st.title("📞 Contact")
    st.write("Reach out at contact@example.com")


pg = st.navigation([
    st.Page(home, title="Home"),
    st.Page(authors, title="Authors"),
    st.Page(writing_evaluation, title="Evaluate"),
    st.Page(about, title="Rubric"),
    st.Page(contact, title="Contact")
])


def display_rubric():
    st.title(":scroll: 826 Valencia Grading Rubric")
    st.subheader(
        "📖 This rubric outlines the key criteria for evaluating student writing.")

    # Define the rubric with CSS that adapts to light and dark mode
    rubric_html = """
    <style>
        /* Use Streamlit's built-in theme variables */
        :root {
            --background-light: #ffffff;
            --background-dark: #262730;
            --text-light: #000000;
            --text-dark: #ffffff;
            --border-light: #ddd;
            --border-dark: #444;
        }
        
        @media (prefers-color-scheme: dark) {
            table { background-color: var(--background-dark); color: var(--text-dark); }
            th, td { border-color: var(--border-dark); }
            th { background-color: #333; }
        }

        @media (prefers-color-scheme: light) {
            table { background-color: var(--background-light); color: var(--text-light); }
            th, td { border-color: var(--border-light); }
            th { background-color: #f4f4f4; }
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 16px;
            text-align: left;
        }
        th, td {
            border: 1px solid;
            padding: 12px;
            word-wrap: break-word;
        }
        td {
            vertical-align: top;
        }
    </style>
    
    <table>
        <tr>
            <th>Criterion</th>
            <th>Exceptional (5)</th>
            <th>Experienced (4)</th>
            <th>Proficient (3)</th>
            <th>Emerging (2)</th>
            <th>Beginning (1)</th>
        </tr>
        <tr>
            <td><b>Ideas & Content</b></td>
            <td>I have a clear, focused, important, and fully developed main idea, with original thoughts and opinions.</td>
            <td>I have a clear, focused, and fully developed main idea, but can share my own thoughts and opinions more creatively.</td>
            <td>I have a generally clear, focused, and accurate main idea, but I need to share creative ideas.</td>
            <td>I have a focus, but I need to make my main idea clearer.</td>
            <td>I started my writing, but I need to add ideas connected to the topic.</td>
        </tr>
        <tr>
            <td><b>Organization</b></td>
            <td>I have a clear purpose, satisfying conclusion, and use thoughtful, varied language to keep the reader's attention.</td>
            <td>I have a clear purpose throughout my writing and use transitions to connect different ideas, but my writing needs more variety. My ideas are separated into different paragraphs.</td>
            <td>I have sentences that make sense together, but I need to cover the main ideas clearly in paragraphs with purposeful transitions.</td>
            <td>I have sentences but I need to organize my ideas into a clear paragraph and add transitions. </td>
            <td>I have sentences, but I can organize them better so they make more sense. </td>
        </tr>
        <tr>
            <td><b>Voice</b></td>
            <td>I have a strong tone that supports my topic and engages the reader, and I consistently use a variety of techniques to enhance the flavor of my writing.</td>
            <td>I use a tone that supports my topic and engages my reader, but my writing needs to explore my perspective more and consider the audience.</td>
            <td>I have shown some of my personality and opinions, but I need to add more flavor and hook the reader more.</td>
            <td>I shared my opinion, but I can express how I feel about the topic better.</td>
            <td>I have sentences, but I need to express my opinion.</td>
        </tr>
        <tr>
            <td><b>Word Choice</b></td>
            <td>I use strong and specific words to create imagery for my reader, but I can add more powerful/varied  types of figurative language.</td>
            <td>I use a variety of vocabulary, but I can choose more specific words and figurative language to create an image in my reader's mind.</td>
            <td>I have juicy vocabulary that makes sense, but I can include some figurative language.</td>
            <td>I have some juicy words, but I can add more juicy words that fit.</td>
            <td>I have ideas, but I need to make sure I use the right words without repeating.</td>
        </tr>
        <tr>
            <td><b>Sentence Fluency</b></td>
            <td>I have well-structured sentences with strong rhythm and cadence, and I use varied words/phrases to enhance the flow of the overall writing.</td>
            <td>I have sentences with rhythm and my ideas flow well between one and the next, but I could use more complex sentences to move the piece forward.</td>
            <td>I have a variety of sentence beginnings, but I can create more variety in my sentence types for more flow and rhythm.</td>
            <td>I have sentences that make sense, but I can try using complex and compound sentences.</td>
            <td> have complete sentences, but they can be reorganized to help my reader understand them better.</td>
        </tr>
        <tr>
            <td><b>Conventions</b></td>
            <td>My writing is error-free and my choices in punctuation and grammar contribute to the creativity and clarity of the piece. </td>
            <td>I consistently use correct spelling, punctuation, and grammar, but could introduce a variety of punctuation.</td>
            <td>My sentences make sense. I have mostly used correct spelling and punctuation, but there are minor errors.</td>
            <td>I have sentences and the reader understands some of what I'm saying, but I have some errors that make my writing hard to understand.</td>
            <td>I have ideas, but I need to add periods and capital letters. </td>
        </tr>
    </table>
    """

    # Display the table in Streamlit
    st.markdown(rubric_html, unsafe_allow_html=True)


pg.run()
