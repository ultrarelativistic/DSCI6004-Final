import re
import random

import srt_parser
import IR.tfidf
import datetime
import time
from datetime import timedelta

class Mrrogers_Tfidf:
    _corpus = None
    _tfidf = None

    def __init__(self, di_corpus=None):
        if di_corpus is None:
            self._corpus = srt_parser.Srt_Parser()
        else:
            self._corpus = di_corpus

        self._tfidf = IR.tfidf.TFIDF()
        self._tfidf.read_data(self._corpus.episodes)
        self._tfidf.index()
        self._tfidf.compute_tfidf()

    # main routine to process requests
    def analyze(self, statement):
        print("CLASS: Mrrogers_Tfidf, METHOD: Analyze")
        print("statement", statement)
        statement = statement.lower()

        # hard coded commands
        # TODO: encapsulate commands in rule based engine?
        if "episodes" in statement:
            return self._command_episode()
        if statement.startswith("transcript of"):
            return self._command_transcript_of_episode(statement)
        if "help" in statement:
            return self._command_help()
        if "hello" in statement or "hi" == statement:
            return self._command_hello()
        if "credits" in statement:
            return self._command_credits()
        if "popular words" in statement:
            return self._command_popular_words()

        # Match user's input to responses in psychobabble. Then reflect candidate response."
        responses = self._tfidf.query_rank(statement)

        # if we have a query use it
        if len(responses)>0:
            item = responses[0]
            document_id = item[0]
            segments = dict(item[1][1])
            response_word = random.choice(list(segments.keys()))

            # retrieve the document
            document_of_episode = self._corpus.episodes[document_id]
            indexes_of_response_word = [n for n, value in enumerate(document_of_episode.words_stemmed) if value == response_word] # TODO: this is not completely right. see bug test_analyze_tabl
            index_of_response_word = random.choice(indexes_of_response_word)
            timing_of_segment = document_of_episode.timing[index_of_response_word]
            dt_start_time = timing_of_segment[0]
            dt_end_time = timing_of_segment[1]
            dt_start_time = dt_start_time - timedelta(seconds=30)
            dt_end_time = dt_end_time + timedelta(seconds=30)

            # check boundry points
            if dt_start_time.hour == 12:
                dt_start_time = document_of_episode.timing[0]
            if dt_end_time > document_of_episode.timing[-1][1]:
                dt_end_time == document_of_episode.timing[-1]

            # create url based off of start and end time
            # https://developers.google.com/youtube/player_parameters
            converter = lambda dt: dt.minute*60 + dt.second
            url = "https://youtube.com/embed/{0}?autoplay=1&start={1}&end={2}"
            url = url.format(document_of_episode.youtubeurl, converter(dt_start_time), converter(dt_end_time))
            response_message = [url]
        else:
            # else show a puppet show with an apology
            response_message = ["Sorry I don't know about that. Try 'tell me about purple panda'. In the meantime, enjoy this puppet show! https://youtube.com/embed/VyLgiPItJj0?autoplay=1&start=646&end=999"]

        # return the response
        response = random.choice(response_message)
        print("analyze complete")
        return response

    # helper method
    def _command_episode(self):
        response = "episode id : episode name\n"
        for n, episode in enumerate(self._corpus.episodes):
            response += "{0} : {1}\n".format(n, episode.name)
        response += "Hint: 'transcript of episode (XX)'."
        return response

    # helper method
    def _command_transcript_of_episode(self, statement):
        response = None
        try:
            print(statement)
            match_group = re.search(r"(\d+)", statement, re.IGNORECASE)
            print(match_group)
            capture_group = match_group.groups(0)[0] if len(match_group.groups()) > 0 else ""
            episode_id = int(capture_group)
            episode = self._corpus.episodes[episode_id]
            response = "{0}\n{1}".format(episode.name, episode.words_unaltered)
        except Exception as err:
            print(err)
            response = "I am sorry neighbor, I didn't understand which episode id you wanted"
        finally:
            pass
        return response

    # helper method
    def _reflect(self, fragment):
        fragment = fragment.lower()
        tokens = fragment.split(" ")
        tokens = list(map(lambda x: self.reflections[x] if x in self.reflections else x, tokens))
        return ' '.join(tokens)

    def _command_help(self):
        s = "Try words 'episodes', 'transcript of episode (XX)'," \
            "'popular words', 'history', 'credits'. "
        return s

    def _command_hello(self):
        s = "It's a beautiful day in this neighborhood, \n" + \
            "A beautiful day for a neighbor. \n" + \
            "Would you be mine? \n" + \
            "Could you be mine? \n" + \
            "https://youtube.com/embed/VyLgiPItJj0?autoplay=1&start=0&end=90 \n" + \
            "Type 'help' for instructions."
        return s

    def _command_credits(self):
        s = "This project initially started by my final project for NLP and AI classes. Thanks for the support. Joseph Miguel"
        return s

    def _command_popular_words(self):
        result = self._tfidf.get_vocab_with_score()
        result = result[0:25]  # only take the first 25
        result = [(_[0][0], list(_[0][1][1].keys())[0]) for _ in result]  # hack bad data structure. tulip of document id & stemmed word
        result = [(_[0], self._corpus.episodes[_[0]].words_stemmed.index(_[1])) for _ in result]  # hack
        result = [(_[0], self._corpus.episodes[_[0]].words[_[1]]) for _ in result]  # hack
        result = [k[1] for k in result]  # hack
        s = " ".join(result)
        return s

