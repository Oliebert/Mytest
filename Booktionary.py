# !/bin/python3
# -*- coding: utf-8 -*-
import gzip
import os
import struct
from collections import namedtuple, defaultdict
import io
import itertools
from os import path
import codecs

import kivy.app
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
import Converter
from os.path import isfile, splitext

IndexEntry = namedtuple('IndexEntry', ('offset', 'size'))

DefinitionPartType = namedtuple('DefinitionPartType',
                                ('TEXT', 'HTML'))('m', 'h')
DefinitionPart = namedtuple('DefinitionPart', ('type', 'data'))


class Dictionary:  # GithHub Library
    def __init__(self, ifo_path):
        # type: (object) -> object
        self.path = ifo_path
        self._config = self._load_dict_config(ifo_path)

        dict_root = path.splitext(ifo_path)[0]
        self._index = self._load_word_list(dict_root)

        try:
            # TODO: it might be better to use some kind of `dictzip` module
            #     here
            self._definitions_file = gzip.open(dict_root + '.dict.dz', 'rb')
        except IOError:
            self._definitions_file = io.open(dict_root + '.dict', 'rb')

    def _load_dict_config(self, ifo_path):
        with io.open(ifo_path, encoding='utf-8') as config_file:
            # Discard thheade header
            config_file.readline()

            config = dict(line.rstrip().split('=', 1) for line in config_file)

        return config

    def _load_syn_list(self, dict_root):
        try:
            syn_list_file = io.open(dict_root + '.syn', 'rb')
        except IOError:
            return {}

        syn_index_map = defaultdict(list)

        with syn_list_file:
            syn_list = syn_list_file.read()

        i = 0

        while i < len(syn_list):
            j = i

            while syn_list[i] != 0x00:
                i += 1

            key = syn_list[j:i].decode('utf-8')
            original_word_index = struct.unpack('>I', syn_list[(i + 1):(i + 5)])[0]

            syn_index_map[original_word_index].append(key)

            i += 5

        return syn_index_map

    def _load_word_list(self, dict_root):
        try:
            index_file = io.open(dict_root + '.idx', 'rb')
        except IOError:
            index_file = gzip.open(dict_root + '.idx.gz', 'rb')

        with index_file:
            word_list = index_file.read()

        # The size of the offset field depends on the idxoffsetbits
        # setting: it may be either 32 (the default) or 64 bits. The
        # size field is always 4 bytes. We initialise the function used
        # to extract the metadata stored in those fields appropriately.
        if self._config.get('idxoffsetbits', '32') == '64':
            meta_size = 12
            unpack_meta = struct.Struct('>QI').unpack
        else:
            meta_size = 8
            unpack_meta = struct.Struct('>II').unpack

        index = defaultdict(list)
        syn_index_map = self._load_syn_list(dict_root)

        i = n = 0

        while i < len(word_list):
            j = i

            while i < len(word_list) and word_list[i] != "\0" and word_list[i] != 0x00:
                i += 1

            entry = IndexEntry(*unpack_meta(
                word_list[(i + 1):(i + 1 + meta_size)]))
            index[word_list[j:i].decode('utf-8')].append(entry)

            if n in syn_index_map:
                for key in syn_index_map[n]:
                    index[key].append(entry)

            i += 1 + meta_size
            n += 1

        # We don't need the index to be a `defaultdict` anymore
        index.default_factory = None

        return index

    def _read_definition_part(self, part_type, definition_data):
        return bytearray(itertools.takewhile(lambda byte: byte != 0x00,
                                             definition_data)).decode('utf-8')

    def __len__(self):
        return len(self._index)

    def __iter__(self):
        return iter(self._index)

    def __getitem__(self, word):
        for entry in self._index[word]:
            self._definitions_file.seek(entry.offset)
            definition_data = \
                iter(self._definitions_file.read(entry.size))

            if 'sametypesequence' in self._config:
                for part_type in self._config['sametypesequence']:
                    yield DefinitionPart(part_type,
                                         self._read_definition_part(part_type, definition_data))
            else:
                raise NotImplementedError

    def words(self):

        return self._index.keys()


class Load_Dictionary_Screen(Screen):
    
    def load_dic(self,path, filename):
        """

        :type filename: object
        """
        new_dic = os.path.join(path, filename[0])

        sm.get_screen(
            'Main_Screen').ids.DictLoadButton.dict_path = new_dic  # get_screen - gibt Text aus einen anderen Screen zurück

        sm.current = 'Main_Screen'  # kehrt zu main Screen zurück

    #def selected(self, new_dic):
     #   print ("selected: %s" % new_dic)


def get_words_from_text(text):  # nimmt den ganzen Text und trennt den in die Wörter

    splitline = text.split()

    return splitline


count = {}


def sort_words_by_frequency(words):  # sortiert die Wörter nach Häufigkeit
    for i in words:

        i = i.lower()

        if i in count:

            count[i] = count[i] + 1

        else:

            count[i] = 1  

    gefiltert = sorted(count.items(), key=lambda x: x[1], reverse=True)

    return gefiltert


class Main_Screen(Screen):
    def button_pressed(self):

        dic_path = self.ids.DictLoadButton.dict_path
        dic = Dictionary(dic_path)

        filename_2 = self.ids.loadfile.filename_2
       # Converter.Converter_1(filename_2)

        textline = self.ids.T1.text  # Zugriff auf class Main_Screen, TextInput, id: text
        words = get_words_from_text(textline)
        srt = sort_words_by_frequency(words)
        word1 = ""
        word2 = ""
        for word in srt:

            word = next(iter(word))  # it returns the next value from the iterator, trennt sets in Wörter

            word1 = word1 + word + "\n"  # every Word from new line

            if word in dic:

                for entry in dic[word]:
                    word2 = word2 + entry.data  # add translation

        self.ids.T2.text = word2


class Load_file_Screen(Screen):
    def open_file(self, path, filename):
        text_path = os.path.join(path, filename[0])
        file_name = os.path.basename(text_path)  # gibt filename zurück
                                                 # get_screen - gibt Text aus einen anderen Screen zurück
        if file_name.endswith('.txt'):

            sm.get_screen('Main_Screen').ids.loadfile.filename_2 = file_name

            with open(os.path.join(path, filename[0])) as f:
                sm.get_screen(
                    'Main_Screen').ids.T1.text = f.read()  # get_screen - gibt Text aus einen anderen Screen zurück
                sm.current = 'Main_Screen'  # kehrt zu main Screen zurück

        else:
            ofname, iftype = splitext(file_name)[0] + '.txt', splitext(file_name)[1].lower()
            con = Converter.Converter()
            if iftype == '.doc':
                con.doc_txt(file_name, ofname)
            elif iftype == '.docx':
                con.docx_txt(file_name, ofname)
            elif iftype == '.odt':
                con.odt_txt(file_name, ofname)
            elif iftype in ('.fb2', '.html', '.htm'):
                con.fb2_txt(file_name, ofname)

            sm.get_screen('Main_Screen').ids.loadfile.filename_2 = ofname



    def selected(self, filename):
        # type: (object) -> object
        print ("selected: %s" % filename[0])



class Save_translation_Screen(Screen):
    def save(self, path, filename):
        with io.open(os.path.join(path, filename), 'w') as f:
            f.write(sm.get_screen('Main_Screen').ids.T2.text)
            sm.current = 'Main_Screen'

    def selected(self, filename):
        print ("selected: %s" % filename[0])


root = Builder.load_string('''

#:import FadeTransition kivy.uix.screenmanager.FadeTransition

<Main_Screen>:
    transition: FadeTransition()
    name: 'Main_Screen'
    id: Main_Screen

    BoxLayout:
        orientation: 'vertical'


        BoxLayout:

            id: ButtonBox1
            size_hint_y: None
            height: 50

            Button:

                id: loadfile
                text: "Load file"
                filename_2:""
                a: ""
                on_press:app.root.current = 'Load_file_Screen'


            Button:

                id: savefile
                text: "Save translations"
                on_press:app.root.current = 'Save_translation_Screen'
                font_size:14

        BoxLayout:

            id: ButtonBox2

            TextInput:

                id: T1
                text: " "
                multiline: True

            TextInput:

                id: T2
                text: " "
                multiline: True

        BoxLayout:
            id: ButtonBox3
            size_hint_y: None
            height: 50



            Button:
                id: DictLoadButton
                text: "Load Dictionary"
                dict_path: ""

                on_press:app.root.current = 'Load_Dictionary_Screen'

            Button:

                text: "Create collection"
                on_press:Main_Screen.button_pressed()


<Load_file_Screen>:
    id:Load_file_Screen # variablen für den Zugriff
    name:'Load_file_Screen'

    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserIconView:
            id: filechooser


        BoxLayout:
            size_hint_y: None
            height: 30
            Button:
                text: "Cancel"
                on_release: app.root.current = 'Main_Screen'

            Button:
                text: "open"
                on_release: Load_file_Screen.open_file(filechooser.path, filechooser.selection)


<Save_translation_Screen>: #Class rule
    id:Save_translation_Screen

    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserIconView:
            id: filechooser
            on_selection: text_input.text = self.selection and self.selection[0] or ''

        TextInput:
            id: text_input
            size_hint_y: None
            height: 30
            multiline: False

        BoxLayout:
            size_hint_y: None
            height: 30
            Button:
                text: "Cancel"
                on_release: app.root.current = 'Main_Screen'

            Button:
                text: "Save"
                on_release: Save_translation_Screen.save(filechooser.path, text_input.text)

<Load_Dictionary_Screen>:
    id:Load_Dictionary_Screen # variablen für den Zugriff
    name:'Load_Dictionary_Screen'

    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserIconView:
            id: filechooser


        BoxLayout:
            size_hint_y: None
            height: 30
            Button:
                text: "Cancel"
                on_release: app.root.current = 'Main_Screen'

            Button:
                text: "load"

                on_release: Load_Dictionary_Screen.load_dic(filechooser.path, filechooser.selection)



''')

sm = ScreenManager()

sm.add_widget(Main_Screen(name='Main_Screen'))

sm.add_widget(Load_file_Screen(name='Load_file_Screen'))

sm.add_widget(Save_translation_Screen(name='Save_translation_Screen'))

sm.add_widget(Load_Dictionary_Screen(name='Load_Dictionary_Screen'))


class Whatever(kivy.app.App):
    def build(self):  # Initializieren und Zurückgeben die Root Widgets:

        return sm


if __name__ == '__main__':
    Whatever().run()
