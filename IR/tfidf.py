#!/usr/bin/env python
import json
import math
import os
import re
import sys
import heapq
import IR.PorterStemmer


class TFIDF:

    def __init__(self):
        # For holding the data - initialized in read_data()
        self.titles = []
        self.docs = []
        self.vocab = []
        # For the text pre-processing.
        self.re_alphanum = re.compile(r'[^a-zA-Z0-9]')
        self.p = IR.PorterStemmer.PorterStemmer()

    # private?
    def get_uniq_words(self):
        uniq = set()
        for doc in self.docs:
            for word in doc:
                uniq.add(word)
        return uniq

    def __read_raw_data(self, episodes):
        print("Stemming Documents...")

        titles = []
        docs = []
        for episode in episodes:
            contents = []
            for word in episode.words:
                # make sure everything is lower case
                word = word.lower()
                # split on whitespace
                # remove non alphanumeric characters
                word = self.re_alphanum.sub('', word)
                # remove any words that are now empty
                line = word if word is not '' else "asdfasdfasdfasdfasf"
                # stem words
                word = self.p.stem(word)
                # add to the document's conents
                contents.extend([word])
            titles.append(episode.name)
            docs.append(contents)
        print("Complete")
        return titles, docs

    # private?
    def read_data(self, episodes):
        """
        Given the location of the 'data' directory, reads in the documents to
        be indexed.
        # """
        # # NOTE: We cache stemmed documents for speed
        # #       (i.e. write to files in new 'stemmed/' dir).
        #
        # print("Reading in documents...")
        # # dict mapping file names to list of "words" (tokens)
        # filenames = os.listdir(dirname)
        # subdirs = os.listdir(dirname)
        # if 'stemmed' in subdirs:
        #     titles, docs = self.__read_stemmed_data(dirname)
        # else:
        titles, docs = self.__read_raw_data(episodes)
        #
        # # Sort document alphabetically by title to ensure we have the proper
        # # document indices when referring to them.
        # ordering = [idx for idx, title in sorted(enumerate(titles),
        #     key = lambda xx : xx[1])]

        self.titles = titles
        self.docs = docs
        # numdocs = len(docs)
        # for d in range(numdocs):
        #     self.titles.append(titles[ordering[d]])
        #     self.docs.append(docs[ordering[d]])

        # Get the vocabulary.
        self.vocab = [xx for xx in self.get_uniq_words()]

    # public
    def compute_tfidf(self):
        # -------------------------------------------------------------------
        # TODO: Compute and store TF-IDF values for words and documents.
        #       Recall that you can make use of:
        #         * self.vocab: a list of all distinct (stemmed) words
        #         * self.docs: a list of lists, where the i-th document is
        #                   self.docs[i] => ['word1', 'word2', ..., 'wordN']
        #       NOTE that you probably do *not* want to store a value for every
        #       word-document pair, but rather just for those pairs where a
        #       word actually occurs in the document.
        print('Calculating tf-idf...')
        self.tfidf = {}
        logN = math.log(len(self.docs), 10)
        for word in self.vocab:
            # word_doc_indexes = index of doc containing word: offsets of word in doc
            word_doc_indexes = self.inv_index[word]
            idf = logN - math.log(len(word_doc_indexes), 10)
            for d, offsets in word_doc_indexes.items():
                if word not in self.tfidf:
                    self.tfidf[word] = {} # Empty placeholder value; Like null
                tf = 1.0 + math.log(len(offsets), 10)
                self.tfidf[word][d] = tf * idf

        # Calculate per-document l2 norms for use in cosine similarity
        # self.tfidf_l2norm[d] = sqrt(sum[tdidf**2])) for tdidf of all words in document number d
        tfidf_l2norm2 = {}
        for word, d_dict in self.tfidf.items():
            for d, val in d_dict.items():
                tfidf_l2norm2[d] = tfidf_l2norm2.get(d, 0.0) + val ** 2
        self.tfidf_l2norm = dict((k,math.sqrt(v)) for k,v in tfidf_l2norm2.items())
        print("Complete")
        # ------------------------------------------------------------------

    # private?
    def get_tfidf(self, word, document):
        # ------------------------------------------------------------------
        # TODO: Return the tf-idf weighting for the given word (string) and
        #       document index.
        return self.tfidf[word][document]
        # ------------------------------------------------------------------

    # private?
    def get_tfidf_unstemmed(self, word, document):
        """
        This function gets the TF-IDF of an *unstemmed* word in a document.
        Stems the word and then calls get_tfidf. You should *not* need to
        change this interface, but it is necessary for submission.
        """
        word = self.p.stem(word)
        return self.get_tfidf(word, document)

    # private?
    def index(self):
        """
        Build an index of the documents.
        Inverted index is
            word index : title index : list of offsets of word in doc[title index]
        """
        print('Indexing...')
        # ------------------------------------------------------------------
        # TODO: Create an inverted index.
        #       Granted this may not be a linked list as in a proper
        #       implementation.
        #       Some helpful instance variables:
        #         * self.docs = List of documents
        #         * self.titles = List of titles

        inv_index = {}

        for i, title in enumerate(self.titles):
            for j, word in enumerate(self.docs[i]):

                if not word in inv_index:
                    inv_index[word] = {}

                if not i in inv_index[word]:
                    inv_index[word][i] = []

                inv_index[word][i].append(j)

        self.inv_index = inv_index
        print("Complete")
        # ------------------------------------------------------------------

    # private?
    def get_posting(self, word):
        """
        Given a word, this returns the list of document indices (sorted) in
        which the word occurs.
        """
        # ------------------------------------------------------------------
        # TODO: return the list of postings for a word.
        return self.inv_index[word].keys()
        # ------------------------------------------------------------------

    # private?
    def get_posting_unstemmed(self, word):
        """
        Given a word, this *stems* the word and then calls get_posting on the
        stemmed word to get its postings list. You should *not* need to change
        this function. It is needed for submission.
        """
        word = self.p.stem(word)
        return self.get_posting(word)

    # private?
    def boolean_retrieve(self, query):
        """
        Given a query in the form of a list of *stemmed* words, this returns
        the list of documents in which *all* of those words occur (ie an AND
        query).
        Return an empty list if the query does not return any documents.
        """
        # ------------------------------------------------------------------
        # TODO: Implement Boolean retrieval. You will want to use your
        #       inverted index that you created in index().
        # Right now this just returns all the possible documents!

        matches = set([i for i in range(len(self.titles))])
        for word in query:
            matches &= set(self.inv_index[word].keys())
        return matches
        # ------------------------------------------------------------------

    # private?
    def rank_retrieve(self, query):
        """
        Given a query (a list of words), return a rank-ordered list of
        documents (by ID) and score for the query.

        return <tuple> (document_id, <tuple>(total score, score of each word))
        return <class 'tuple'>: (1, (0.14681049969648288, {'almost': 0.4446578049034344, 'adult': 0.3916490539534377}))
        """

        # Construct the query vector as a dict word:log(tf)
        query_vec = {}
        for word in query:
            query_vec[word] = query_vec.get(word,0) + 1
        query_vec = dict((word, math.log(query_vec[word], 10) + 1.0) for word in query_vec)

        def get_score(d):
            """Return score for document d
                This is cos(query_vec * d_vec/norm) where
                    d_vec[word] = tfidf of word in doc number d
                    norm = sqrt(d_vec[w]**2) for all words w in doc number d
            """
            d_vec = dict((word, self.tfidf[word].get(d, 0.0)) for word in query_vec if word in self.tfidf)
            r = sum(query_vec[word] * d_vec[word] for word in d_vec)/self.tfidf_l2norm[d]
            return (r, d_vec)

        # Compute scores and add to a priority queue
        scores = []
        for d in range(len(self.docs)):
            heapq.heappush(scores, (get_score(d), d))

        result = [(k,v) for v,k in heapq.nlargest(10,scores) if v[0]>0] # Return top 10 scores and scores of zero
        return result

    # private?
    def process_query(self, query_str):
        """
        Given a query string, process it and return the list of lowercase,
        alphanumeric, stemmed words in the string.
        """
        # make sure everything is lower case
        query = query_str.lower()
        # split on whitespace
        query = query.split()
        # remove non alphanumeric characters
        query = [self.re_alphanum.sub('', xx) for xx in query]
        # stem words
        query = [self.p.stem(xx) for xx in query]
        return query

    # private?
    def query_retrieve(self, query_str):
        """
        Given a string, process and then return the list of matching documents
        found by boolean_retrieve().
        """
        query = self.process_query(query_str)
        return self.boolean_retrieve(query)



    # public method
    def get_vocab_with_score(self):
        """
        return a sorted rank-ordered list of all words in it's vocab
        documents (by ID) and score for the query.

        return <tuple> (document_id, <tuple>(total score, score of each word))
        return <class 'tuple'>: (1, (0.14681049969648288, {'almost': 0.4446578049034344, 'adult': 0.3916490539534377}))
        """
        result = [self.query_rank(_) for _ in self.vocab]
        result = [_ for _ in result if len(_)>0] # workaround, list entries should never be len()==0
        result = sorted(result, key=lambda x:x[0][1][0], reverse=True) # sorted off total score
        return result

    # public method
    def query_rank(self, query_str):
        """
        Given a string, process and then return the list of the top matching
        documents, rank-ordered.
        """
        query = self.process_query(query_str)
        return self.rank_retrieve(query)

