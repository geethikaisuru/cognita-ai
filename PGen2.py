import fitz  # PyMuPDF
import nltk
import sys
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import spacy
from gensim import corpora
from gensim.models import LdaModel
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests
import json
import textwrap
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors
import os

print("Successfully imported all libraries")

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

def extract_text_from_pdfs(pdf_files):
    text = ""
    for pdf_file in pdf_files:
        doc = fitz.open(pdf_file)
        for page in doc:
            text += page.get_text()
        doc.close()
    print(f"Extracted text sample: {text[:200]}...")
    return text

def preprocess_text(text):
    # Remove headers, footers, and page numbers
    lines = text.split('\n')
    cleaned_lines = [line for line in lines if not re.match(r'^\s*\d+\s*$', line)]  # Remove page numbers
    text = '\n'.join(cleaned_lines)
    
    # Handle hyphenated words
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove numbering and special characters
    text = re.sub(r'\d+\.|\(|\)', '', text)
    
    # Tokenize into sentences
    sentences = sent_tokenize(text)
    
    # Tokenize words and remove stopwords
    stop_words = set(stopwords.words('english'))
    preprocessed_sentences = []
    for sentence in sentences:
        tokens = word_tokenize(sentence.lower())
        tokens = [token for token in tokens if token.isalnum() and token not in stop_words]
        preprocessed_sentences.append(' '.join(tokens))
    
    return preprocessed_sentences

def extract_questions(text):
    # Implement more robust question detection
    questions = re.findall(r'\d+\.\s*(.*?\?)', text, re.DOTALL)
    return questions

def analyze_questions(questions):
    nlp = spacy.load("en_core_web_sm")
    
    analyzed_questions = []
    for question in questions:
        doc = nlp(question)
        entities = [ent.text for ent in doc.ents]
        pos_tags = [token.pos_ for token in doc]
        analyzed_questions.append({
            'text': question,
            'entities': entities,
            'pos_tags': pos_tags
        })
    
    return analyzed_questions

def identify_topics(preprocessed_text):
    dictionary = corpora.Dictionary([text.split() for text in preprocessed_text])
    corpus = [dictionary.doc2bow(text.split()) for text in preprocessed_text]
    lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=5, random_state=100)
    topics = lda_model.print_topics()
    return [topic for _, topic in topics]  # Return only the topic strings, not the topic numbers


def generate_questions(context, num_questions, analyzed_questions):
    generated_questions = []
    for i in range(num_questions):
        # Create a more specific prompt
        prompt = f"""Generate a new exam question based on the following context and guidelines:

Context: {context[:500]}  # Limit context to 500 characters

Guidelines:
1. The question should be similar in style and complexity to this example: {random.choice(analyzed_questions)['text']}
2. Ensure the question ends with a question mark.
3. The question should be thought-provoking and require critical thinking.
4. Avoid yes/no questions.
5. The question should be relevant to the given context.

Generated Question:"""

        response = requests.post('http://localhost:11434/api/generate', 
                                 json={
                                     "model": "phi3:mini",
                                     "prompt": prompt,
                                     "stream": False
                                 })
        
        if response.status_code == 200:
            question = response.json()['response'].strip()
            generated_questions.append(question)
        else:
            print(f"Error generating question: {response.status_code}")
    
    print(f"Generated {len(generated_questions)} questions")
    return generated_questions

def filter_and_rank_questions(generated_questions, analyzed_questions, topics):
    filtered_questions = []
    for question in generated_questions:
        processed_question = post_process_question(question)
        if len(processed_question.split()) >= 10 and processed_question not in filtered_questions:
            filtered_questions.append(processed_question)
    
    # Implement a basic ranking based on similarity to original questions and topic coverage
    ranked_questions = sorted(filtered_questions, 
                              key=lambda q: max(similarity(q, aq['text']) for aq in analyzed_questions), 
                              reverse=True)
    
    # Ensure topic coverage
    final_questions = []
    covered_topics = set()
    for question in ranked_questions:
        question_topics = set(word for topic in topics for word in topic.split('+') if word in question.lower())
        if question_topics - covered_topics:
            final_questions.append(question)
            covered_topics.update(question_topics)
        if len(final_questions) == len(analyzed_questions):
            break
    
    print(f"Filtered and ranked to {len(final_questions)} questions")
    return final_questions
def similarity(q1, q2):
    # Implement a basic similarity measure (you might want to use a more sophisticated method)
    return len(set(q1.lower().split()) & set(q2.lower().split())) / len(set(q1.lower().split()) | set(q2.lower().split()))

def post_process_question(question):
    # Remove any text before the actual question
    question = re.sub(r'^.*?([A-Z])', r'\1', question, flags=re.DOTALL)
    
    # Capitalize the first letter
    question = question.capitalize()
    
    # Ensure the question ends with a question mark
    if not question.endswith('?'):
        question += '?'
    
    return question

def format_question_paper(questions):
    paper = "Model Question Paper\n\n"
    for i, question in enumerate(questions, 1):
        wrapped_question = textwrap.fill(question, width=80, subsequent_indent='    ')
        paper += f"{i}. {wrapped_question}\n\n"
    return paper

def save_as_pdf(text, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(name='Question',
                              parent=styles['Normal'],
                              fontSize=11,
                              leading=14,
                              leftIndent=20,
                              rightIndent=20,
                              firstLineIndent=-20,
                              alignment=TA_JUSTIFY,
                              spaceAfter=12))

    styles['Title'].fontSize = 16
    styles['Title'].alignment = 1
    styles['Title'].spaceAfter = 0.5*inch

    flowables = []

    flowables.append(Paragraph("Model Question Paper", styles['Title']))
    flowables.append(Spacer(1, 0.25*inch))

    questions = [q.strip() for q in text.split('\n\n')[1:] if q.strip() and not q.strip().isdigit()]
    
    for i, question in enumerate(questions, 1):
        q = re.sub(r'^\d+\.\s*', '', question)
        q = f"{i}. {q}"
        flowables.append(KeepTogether(Paragraph(q, styles['Question'])))

    def add_border(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)
        canvas.rect(doc.leftMargin, doc.bottomMargin,
                    doc.width, doc.height, stroke=1, fill=0)
        canvas.restoreState()

    doc.build(flowables, onFirstPage=add_border, onLaterPages=add_border)

print("Completed functions compiling")

def main(pdf_files):
    print("Received file paths:", pdf_files)
    for file in pdf_files:
        if not os.path.exists(file):
            print(f"File not found: {file}")
            raise FileNotFoundError(f"File not found: {file}")
        else:
            print(f"File exists: {file}")
    
    print("Extracting text from PDFs...")
    text = extract_text_from_pdfs(pdf_files)
    print(f"Extracted {len(text)} characters of text")
    
    print("Preprocessing text...")
    preprocessed_text = preprocess_text(text)
    print(f"Preprocessed into {len(preprocessed_text)} sentences")
    
    print("Extracting questions...")
    original_questions = extract_questions(text)
    print(f"Extracted {len(original_questions)} questions")
    
    print("Analyzing questions...")
    analyzed_questions = analyze_questions(original_questions)
    print(f"Analyzed {len(analyzed_questions)} questions")
    
    print("Identifying topics...")
    topics = identify_topics(preprocessed_text)
    print(f"Identified {len(topics)} topics")
    
    print("Generating questions...")
    generated_questions = generate_questions(' '.join(preprocessed_text), num_questions=len(analyzed_questions) * 2, analyzed_questions=analyzed_questions)
    
    print("Filtering and ranking questions...")
    final_questions = filter_and_rank_questions(generated_questions, analyzed_questions, topics)
    
    print("Formatting question paper...")
    final_paper = format_question_paper(final_questions)
    
    print("Saving question paper as PDF...")
    save_as_pdf(final_paper, "improved_model_paper.pdf")
    
    return final_paper

if __name__ == "__main__":
    pdf_files = sys.argv[1:]
    model_paper = main(pdf_files)
    print("Model paper generation complete. Output saved as 'improved_model_paper.pdf'.")
    print("\nGenerated Model Paper:")
    print(model_paper)