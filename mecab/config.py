import os
import subprocess
import sys
import pandas as pd

from contextlib import contextmanager
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from collections import namedtuple
from pathlib import Path


DicEntry = namedtuple('DicEntry', [
    'surface',
    'dummy1',
    'dummy2',
    'dummy3',
    'pos',
    'semantic',
    'has_jongseong',
    'reading',
    'type',
    'start_pos',
    'end_pos',
    'expression'
    ], 
    defaults=[
        None,None,None,None,'NNP','*','T',None,'*','*','*','*'
])


@contextmanager
def change_directory(directory):
    original = os.path.abspath(os.getcwd())
    
    fancy_print(' Change directory to {}'.format(directory))
    os.chdir(directory)
    yield

    fancy_print(' Change directory back to {}'.format(original))
    os.chdir(original)

def path_of(filename):
    for path, _, filenames in os.walk(os.getcwd()):
        if filename in filenames:
            return Path(path)

    raise ValueError('File {} not found'.format(filename))

def fancy_print(*args, color=None, bold=False, **kwargs):
    if bold:
        print('\033[1m', end='')

    if color:
        print('\033[{}m'.format(color), end='')

    print(*args, **kwargs)

    print('\033[0m', end='')  # reset

def install(url, *args, environment=None):
    with TemporaryDirectory() as directory:
        with change_directory(directory):
            download(url)
            configure(*args)
            make(environment=environment)
    
def download(url):
    fancy_print('Downloading a file from %s\n' % url)
    components = urlparse(url)
    filename = os.path.basename(components.path)

    subprocess.run([
        'wget',
        '--progress=bar:force:noscroll',
        '--output-document={}'.format(filename),
        url,
    ], check=True)
    subprocess.run(['tar', '-xzf', filename], check=True)
    return filename

def configure(*args):
    fancy_print('Configuring...\n')
    with change_directory(path_of('configure')):
        try:
            subprocess.run(['./autogen.sh'])
        except:
            pass
            
        subprocess.run(['./configure', *args], check=True)

def configure_userdic():
    fancy_print('Adding userdic...\n')
    with change_directory(path_of('add-userdic.sh')):
        try:
            subprocess.run(['./add-userdic.sh'], check=True)
        except:
            pass
            
def make(environment=None):
    fancy_print('Making...\n')
    with change_directory(path_of('Makefile')):
        subprocess.run(['make'], check=True, env=environment)
        subprocess.run(['make', 'install'], check=True, env=environment)

def iternamedtuples(df):
    Row = namedtuple('Row', df.columns)
    for row in df.itertuples():
        yield Row(*row[1:])

def has_jongseong(c):
    return (int((ord(c[-1]) - 0xAC00) % 28) != 0)


class MeCabConfig:
    MECAB_KO_URL = 'https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz'
    MECAB_KO_DIC_URL = 'https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz'
    
    def __init__(self, userdic_path=None):
        self.mecab_src_path = None
        self.mecab_dic_path = None
        if userdic_path:
            self.load_userdic(userdic_path)
        else:
            self.userdic = []

    def load_userdic(self, userdic_path):
        userdic_path = Path(userdic_path)

        if userdic_path.is_dir():
            self.userdic = []
            for f in userdic_path.glob('*.csv'):
                df = pd.read_csv(f, names=DicEntry._fields)
                self.userdic += [e for e in iternamedtuples(df)]        
        else:
            df = pd.read_csv(userdic_path, names=DicEntry._fields)
            self.userdic = [e for e in iternamedtuples(df)]
        print(' No. of user dictionary entires loaded: %d' % len(self.userdic))
        
    def add_entry_to_userdic(self, surface, pos='NNP', 
                             semantic='*', reading=None):
        entry = DicEntry(surface=surface, 
                         pos=pos, 
                         semantic=semantic, 
                         has_jongseong={True: 'T', False: 'F'}.get(has_jongseong(surface)),
                         reading=surface if reading is None else reading)
        self.userdic.append(entry)
    
    def save_userdic(self, save_path):
        if self.userdic:
            df = pd.DataFrame(self.userdic)
            df.to_csv(save_path, header=False, index=False)
            self.userdic_path = save_path
            print('Saved the userdic to {}'.format(save_path))
        else:
            print('No userdic to save...')
               
    def install_mecab(self, url=None, src_path=None):
        if url is None:
            url = self.MECAB_KO_URL
        
        fancy_print('Installing mecab-ko...', color=32, bold=True)
        with TemporaryDirectory() as directory:
            working_dir = src_path if src_path else directory
            with change_directory(working_dir):
                if not src_path:
                    download(url)
                configure('--prefix={}'.format(sys.prefix),
                        '--enable-utf8-only')
                make(environment=None)
    
    def download_mecab(self, download_dir, url=None):
        if url is None:
            url = self.MECAB_KO_URL
        with change_directory(download_dir):
            filename = download(url)
        self.mecab_src_path = Path(download_dir)/filename.split('.tar')[0]
        print('Downloaded mecab source to %s' % self.mecab_src_path)
        
    def download_kodic(self, download_dir, url=None):
        if url is None:
            url = self.MECAB_KO_DIC_URL
        self.download_dir = download_dir        
        with change_directory(download_dir):
            filename = download(url)
        self.mecab_dic_path = Path(download_dir)/filename.split('.tar')[0]
        print('Downloaded mecab dictionary source to {}'.format(
            self.mecab_dic_path))    
        
    def install_kodic(self, url=None, src_path=None, userdic_path=None):
        if url is None:
            url = self.MECAB_KO_DIC_URL
        if userdic_path:
            self.load_userdic(userdic_path)
        
        fancy_print('Installing mecab-ko-dic...', color=32, bold=True)
        mecab_config_path = os.path.join(sys.prefix, 'bin', 'mecab-config')
        with TemporaryDirectory() as directory:
            working_dir = src_path if src_path else directory
            with change_directory(working_dir):
                if not src_path:
                    download(url)
                configure('--prefix={}'.format(sys.prefix),
                            '--with-charset=utf8',
                            '--with-mecab-config={}'.format(mecab_config_path))
                if userdic_path:
                    save_path = path_of('nnp.csv')/'nnp.csv'
                    for f in save_path.parent.glob('*.csv'):
                        f.unlink()
                    print('* Saving userdic to {}'.format(save_path))
                    self.save_userdic(save_path)
                    configure_userdic()                
                make(environment={
                            'LD_LIBRARY_PATH': os.path.join(sys.prefix, 'lib'),
                        })

