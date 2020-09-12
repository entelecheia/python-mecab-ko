import _mecab
import sys
from pathlib import Path
from collections import namedtuple

Feature = namedtuple('Feature', [
    'pos',
    'semantic',
    'has_jongseong',
    'reading',
    'type',
    'start_pos',
    'end_pos',
    'expression',
])


def _create_lattice(sentence):
    lattice = _mecab.Lattice()
    lattice.add_request_type(_mecab.MECAB_ALLOCATE_SENTENCE)  # Required
    lattice.set_sentence(sentence)

    return lattice

# ('합니다',
#   Feature(pos='XSA+EF', semantic=None, has_jongseong=False, reading='합니다', type='Inflect', 
#           start_pos='XSA', end_pos='EF', 
#           expression='하/XSA/*+ᄇ니다/EF/*')),
def _extract_feature(node):
    # Reference:
    # - http://taku910.github.io/mecab/learn.html
    # - https://docs.google.com/spreadsheets/d/1-9blXKjtjeKZqsf4NzHeYJCrr49-nXeRF6D80udfcwY
    # - https://bitbucket.org/eunjeon/mecab-ko-dic/src/master/utils/dictionary/lexicon.py
    
    # feature = <pos>,<semantic>,<has_jongseong>,<reading>,<type>,<start_pos>,<end_pos>,<expression>
    values = node.feature.split(',')
    assert len(values) == 8

    values = [value if value != '*' else None for value in values]
    feature = dict(zip(Feature._fields, values))
    feature['has_jongseong'] = {'T': True, 'F': False}.get(feature['has_jongseong'])

    return Feature(**feature)


class MeCabError(Exception):
    pass


class MeCab:  # APIs are inspried by KoNLPy
    def __init__(self, dic_path=None):
        if dic_path is None:
            dic_path = Path(sys.executable).parents[1]/'lib/mecab/dic/mecab-ko-dic'
            if not dic_path.is_dir():
                dic_path = Path('/usr/local/lib/mecab/dic/mecab-ko-dic')            
        self.dic_path = Path(dic_path)
        
        try:
            self.tagger = _mecab.Tagger('-d %s' % self.dic_path)
        except RuntimeError:
            raise Exception('The MeCab dictionary does not exist at "%s". Is the dictionary correctly installed?\nYou can also try entering the dictionary path when initializing the Mecab class: "Mecab(\'/some/dic/path\')"' % self.dic_path)
        except NameError:
            raise Exception('Check if MeCab is installed correctlly.')
        self.dictionary_info = self.tagger.dictionary_info()
        self.dic_filename = self.dictionary_info.filename

    def parse(self, sentence):
        lattice = _create_lattice(sentence)
        if not self.tagger.parse(lattice):
            raise MeCabError(self.tagger.what())

        return [
            (node.surface, _extract_feature(node))
            for node in lattice
        ]

    def pos(self, sentence, flatten=True, join=False):
        if flatten:
            return [
                surface + '/' + feature.pos 
                if join else (surface, feature.pos) 
                for surface, feature in self.parse(sentence)
            ]
        else:
            res = []
            for surface, feature in self.parse(sentence):
                if feature.expression is None:
                    res.append((surface, feature.pos))
                else:
                    for elem in feature.expression.split('+'):
                        s = elem.split('/')
                        res.append((s[0], s[1]))
            return [s[0] + '/' + s[1] if join else s for s in res]
            
    def morphs(self, sentence, flatten=True):
        return [
            surface 
            for surface, _ in self.pos(sentence, flatten=flatten, join=False)
        ]

    def nouns(self, sentence, flatten=True):
        return [
            surface 
            for surface, pos in self.pos(sentence, flatten=flatten, join=False)
            if pos.startswith('N')
        ]