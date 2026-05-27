import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

print("CourseBridge ASSIST data script is working.")

# Later, this is where we will load ASSIST data
# Example:
# df = pd.read_csv("data/assist_courses.csv")

sample_courses = pd.DataFrame({
    "community_college": ["CCSF", "CCSF", "CCSF"],
    "uc": ["UC Berkeley", "UCLA", "UCSD"],
    "course": ["MATH 110A", "ECON 1", "CS 111B"],
    "requirement": ["Calculus I", "Macroeconomics", "Programming"]
})

print(sample_courses)

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(sample_courses["requirement"])

print("Text data converted for ML.")
print(vectors.shape)