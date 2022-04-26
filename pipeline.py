"""
Pipeline for text processing implementation
"""

import re
from pathlib import Path

import pymorphy2
from pymystem3 import Mystem

from constants import ASSETS_PATH
from core_utils.article import Article


class EmptyDirectoryError(Exception):
    """
    No data to process
    """


class InconsistentDatasetError(Exception):
    """
    Corrupt data:
        - numeration is expected to start from 1 and to be continuous
        - a number of text files must be equal to the number of meta files
        - text files must not be empty
    """


class MorphologicalToken:
    """
    Stores language params for each processed token
    """

    def __init__(self, original_word):
        self.original_word = original_word
        self.normalized_form = ''
        self.tags_mystem = ''
        self.tags_pymorphy = ''

    def get_cleaned(self):
        """
        Returns lowercased original form of a token
        """
        return self.original_word.lower()

    def get_single_tagged(self):
        """
        Returns normalized lemma with MyStem tags
        """
        return f'{self.normalized_form}<{self.tags_mystem}>'

    def get_multiple_tagged(self):
        """
        Returns normalized lemma with PyMorphy tags
        """
        return f'{self.normalized_form}<{self.tags_mystem}>({self.tags_pymorphy})'


class CorpusManager:
    """
    Works with articles and stores them
    """

    def __init__(self, path_to_raw_txt_data: str):
        self.path_to_raw_txt_data = path_to_raw_txt_data
        self._storage = {}
        self._scan_dataset()

    def _scan_dataset(self):
        """
        Register each dataset entry
        """
        path = Path(self.path_to_raw_txt_data)
        digit = re.compile(r'\d+')
        for file in path.glob('*'):
            digit_in_title = digit.match(file.name)
            if not digit_in_title:
                continue
            article_id = int(digit_in_title.group())
            article = Article(None, article_id)
            self._storage[article_id] = article

    def get_articles(self):
        """
        Returns storage params
        """
        return self._storage


class TextProcessingPipeline:
    """
    Process articles from corpus manager
    """

    def __init__(self, corpus_manager: CorpusManager):
        self.corpus_manager = corpus_manager

    def run(self):
        """
        Runs pipeline process scenario
        """
        articles = self.corpus_manager.get_articles().values()
        cleaned_tokens = []
        single_tagged = []
        multiple_tagged = []
        for article in articles:
            raw_text = article.get_raw_text()
            tokens = self._process(raw_text)
            for token in tokens:
                cleaned_tokens.append(token.get_cleaned())
                single_tagged.append(token.get_single_tagged())
                multiple_tagged.append(token.get_multiple_tagged())
            article.save_as(' '.join(cleaned_tokens), 'cleaned')
            article.save_as(' '.join(single_tagged), 'single_tagged')
            article.save_as(' '.join(multiple_tagged), 'multiple_tagged')

    def _process(self, raw_text: str):
        """
        Processes each token and creates MorphToken class instance
        """
        cleaned_text = ' '.join(re.findall(r'[а-яёА-ЯЁ]+', raw_text))
        analyzed_cleaned_text = Mystem().analyze(cleaned_text)
        tokens = []
        morph = pymorphy2.MorphAnalyzer()
        for token in analyzed_cleaned_text:
            if ('analysis' not in token) \
                    or (not token['analysis']) \
                    or ('lex' not in token['analysis'][0]
                        or 'gr' not in token['analysis'][0]):
                continue
            morphological_token = MorphologicalToken(token['text'])
            morphological_token.normalized_form = token['analysis'][0]['lex']
            morphological_token.tags_mystem = token['analysis'][0]['gr']
            morphological_token.tags_pymorphy = morph.parse(token['text'])[0].tag
            tokens.append(morphological_token)
        return tokens


def validate_dataset(path_to_validate):
    """
    Validates folder with assets
    """
    dataset_path = Path(path_to_validate)
    if not dataset_path.exists():
        raise FileNotFoundError
    if not dataset_path.is_dir():
        raise NotADirectoryError
    indices = []
    digit_pattern = re.compile(r'\d+')
    for files in dataset_path.glob('*'):
        digit = digit_pattern.match(files.stem)
        if not digit:
            raise InconsistentDatasetError
        index = int(digit.group())
        if index not in indices:
            indices.append(index)
    if not indices:
        raise EmptyDirectoryError
    previous_index = 0
    for index in indices:
        if index - previous_index != 1 or indices[0] != 1:
            raise InconsistentDatasetError
        previous_index = index
        raw_path = dataset_path / f'{index}_raw.txt'
        meta_path = dataset_path / f'{index}_meta.json'
        if not raw_path.exists() or not meta_path.exists():
            raise InconsistentDatasetError
        with open(raw_path, 'r', encoding='utf-8') as file:
            if not file.read():
                raise InconsistentDatasetError


def main():
    # YOUR CODE HERE
    validate_dataset(ASSETS_PATH)
    corpus_manager = CorpusManager(ASSETS_PATH)
    pipeline = TextProcessingPipeline(corpus_manager)
    pipeline.run()


if __name__ == "__main__":
    main()
