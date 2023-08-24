from typing import Tuple, Dict, Any, List
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
import nltk
import networkx as nx
from nltk.cluster.util import cosine_distance
from nltk.tokenize import sent_tokenize, punkt
import re
import numpy as np


class Tokenizer:

    def __init__(self):
        self.word_tokenizer_func = word_tokenize
        self.sentence_tokenizer_func = sent_tokenize

    # remove non-word characters and split text into separate tokens
    def tokenize(self, text: str) -> List[str]:
        text = " ".join(re.split(r"\W", text))
        # text = "".join(re.split(r"}|\.(?=\s|\W)|,|;|\"|'|\{|\||\\|\?|\!|#|:|/|((?=\s)-(?=\s))", text))
        return self.word_tokenizer_func(text)

    # compute cosine similarity between sentences
    def compute_similarity(self, sent1, sent2):
        sent1, sent2 = [w.lower() for w in sent1], [w.lower() for w in sent2]
        wordbag = list(set(sent1 + sent2))
        v1, v2 = [0] * len(wordbag), [0] * len(wordbag)
        for w in sent1:
            v1[wordbag.index(w)] += 1
        for w in sent2:
            v2[wordbag.index(w)] += 1
        return 1 - cosine_distance(v1, v2)

    # create similarity matrix between all sentences
    def create_similarity_matrix(self, sentences):
        similarity_matrix = np.zeros((len(sentences), len(sentences)))
        for idx in range(similarity_matrix.shape[0]):
            for idx1 in range(similarity_matrix.shape[1]):
                if idx1 != idx:
                    similarity_matrix[idx, idx1] = self.compute_similarity(sentences[idx],
                                                                           sentences[idx1])
        return similarity_matrix

    def summarize(self, text: str, top_n=5) -> str:
        # split text into sentences
        sentences = self.sentence_tokenizer_func(text)
        for sentence in sentences:
            sentence.replace('\W', ' ')
        # compute similarity between sentences based on cosine similarity
        similarity_matrix = self.create_similarity_matrix(sentences)
        # create a similarity graph
        similarity_graph = nx.from_numpy_array(similarity_matrix)
        # assign similarity scores to sentences using pagerank algorithm
        scores = nx.pagerank(similarity_graph)
        # sort by similarity
        ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
        # pick top_n least similar sentences
        top_n = len(ranked_sentences) if len(ranked_sentences) < top_n else top_n
        return " ".join([ranked_sentences[i][1] for i in range(top_n)])


class Parcer_bs:
    def __init__(self, bs: None):
        self.tokenizer = Tokenizer()
        self.soup = bs

    def parse_keywords(self, titles, h1headers, text, index, alpha=0.1):
        tokenized = self.tokenizer.tokenize("".join(titles + [text]))
        words, freqs = np.unique(np.asarray(tokenized), return_counts=True)
        tf = freqs / freqs.sum()
        doc_freq = []
        for i in words:
            if i in index.keywords_to_sites.keys():
                doc_freq.append(len(index.keywords_to_sites[i]))
            else:
                doc_freq.append(0)
        a = np.asarray(doc_freq) + 1
        b = index.sites_num + 1 + alpha * (index.sites_num + 1)
        idf = np.log2(b / a)
        tf_idf = tf * idf
        inds = tf_idf.argsort()
        # returning 5 most important words
        return dict(list(zip(list(words[inds][:5]), list(tf_idf[inds][:5]))))

    def get_soup(self, text):
        self.soup = BeautifulSoup(text, "html.parser")
        titles = self.soup.findAll('title')
        article_headers_h1 = self.soup.findAll('h1')
        article_headers_h2 = self.soup.findAll('h2')
        article_text = self.soup.find('main')
        article_text = self.soup.find('body') if article_text is None else article_text
        # print(self.soup.text)
        return [title.text for title in titles], \
               [h1.text for h1 in article_headers_h1], \
               self.tokenizer.summarize(article_text.text)
