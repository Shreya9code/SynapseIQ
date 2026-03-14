import autogen
from typing import List, Dict
from backend.agents.base_agent import create_agent
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# --- Internal Tool Logic (Embedded to save files) ---
def analyze_trends_internal(papers: List[Dict]) -> str:
    """
    Lightweight trend analysis using TF-IDF + KMeans.
    No heavy embedding models required.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
        
        if not papers or len(papers) < 2:
            return "Not enough data to analyze trends."

        # 1. Prepare Text
        texts = [f"{p.get('title', '')} {p.get('summary', '')}" for p in papers]
        
        # 2. Vectorize (Lightweight)
        vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
        X = vectorizer.fit_transform(texts)
        
        # 3. Cluster
        n_clusters = min(3, len(papers))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(X)
        
        # 4. Format Output for LLM
        clusters = {}
        for i, label in enumerate(kmeans.labels_):
            clusters.setdefault(label, []).append(papers[i]['title'])
            
        result = "Identified Research Clusters:\n"
        for cid, titles in clusters.items():
            result += f"- Theme {cid}: {', '.join(titles)}\n"
            
        return result
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        return f"Error analyzing trends: {str(e)}"

# --- Agent Definition ---
SYSTEM_MESSAGE = """
You are a Research Trend Analyzer.
Your goal is to discover patterns across multiple research papers.
1. Receive a list of paper summaries (Title + Abstract).
2. Use the analyze_trends_internal function to cluster them by topic.
3. Based on the clusters, identify emerging research directions.
4. Output a structured summary of the 'State of the Field'.
"""

def create_trend_analyzer_agent() -> autogen.ConversableAgent:
    # Register the internal function as a tool
    tools = [analyze_trends_internal]
    agent = create_agent("TrendAnalyzer", SYSTEM_MESSAGE, tools=tools)
    return agent