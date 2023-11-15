import vk
import requests
import pandas as pd

import ray
import re

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from pymystem3 import Mystem

import pymorphy2

import gensim
from gensim import corpora

from telethon import TelegramClient
from pyrogram import Client

from collections import Counter

import tkinter as tk
from tkinter import IntVar
from tkinter import messagebox


mystem = Mystem() 
russian_stopwords = set(stopwords.words("russian"))


@ray.remote
def parse_tg():
    api_id = ''
    api_hash = ''
    phone = ''

    with open('tg-channels.txt', 'r') as channels_file:
        channels = channels_file.read().split('\n')

    with Client(phone, api_id, api_hash) as client:

        for channel in channels:

            # Получаем информацию о канале
            channel_info = client.get_chat(channel)
            
            # Получаем сообщения из канала
            messages = client.get_chat_history(channel_info.id, limit=100)

            return_messages = []

            # Парсим и выводим текст каждого сообщения
            for message in messages:
                if message.caption:
                    return_messages.append(message.caption)
    return return_messages


# PARSING FROM VK
@ray.remote
def parse_vk() -> None:
    TOKEN = ''
    version = 5.131
    count = 100

    with open('vk.txt', 'r') as groups_file:
        groups = groups_file.read().split('\n')
 
    return_posts = []
    
    for group in groups:
        response = requests.get(
            'https://api.vk.com/method/wall.get',
            params = {
                'access_token' : TOKEN,
                'v': version,
                'owner_id': -int(group),
                'count': count
                }
        )

        for i in range(100):
            s = response.json()['response']['items'][i]['text']
            if s:
                return_posts.append(s)
    return return_posts


def remove_symbols(text):
    return re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', text).lower()


def preprocess_text(text):
    text = remove_symbols(text)
    tokens = mystem.lemmatize(text.lower())
    tokens = [token for token in tokens if token not in russian_stopwords and token != " " and token not in ['а', 'с', 'это', 'c', 'свой', 'который']]
    
    text = " ".join(tokens)
    
    return text


@ray.remote
def parallel_preprocessing(text):
    return preprocess_text(text)


def get_popular_topics(processed_posts):
    doc_clean = [doc.split() for doc in processed_posts]
    dictionary = corpora.Dictionary(doc_clean)
    doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]

    print('building a model!')

    Lda = gensim.models.LdaModel
    lda_model = Lda(doc_term_matrix, id2word=dictionary, num_topics=5, passes=50)
    #tokens = [word_tokenize(post.lower()) for post in processed_posts]
    #word_frequencies = Counter([token for post_tokens in tokens for token in post_tokens])
    #popular_topics = [word for word, frequency in word_frequencies.items() if frequency > 250]

    return lda_model.print_topics(num_topics=3, num_words=4)


class ProgramInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Program Interface")
        self.geometry("700x400")

        self.create_widgets()


    def create_widgets(self):

        # Quasi-Identifiers entry
        self.quasi_identifiers_label = tk.Label(self, text="Запуск программы")
        self.quasi_identifiers_label.pack()

        self.tg_label = tk.Label(self)

        # Depersonalization button
        self.depersonalize_button = tk.Button(self, text="Start", command=self.depersonalize_dataset)
        self.depersonalize_button.pack(pady=20)


    def depersonalize_dataset(self):
        ray.init()
        print("STARTING")
        messagebox.showinfo('Starting')
        vk_result, tg_result = ray.get([parse_vk.remote(), parse_tg.remote()])

        print("STARTED PREPROCESSING")
        messagebox.showinfo("STARTED PREPROCESSING")

        processed_data_parallel_vk = ray.get([parallel_preprocessing.remote(text) for text in vk_result])
        processed_data_parallel_tg = ray.get([parallel_preprocessing.remote(text) for text in tg_result])
        
        pop_topics_vk = get_popular_topics(processed_data_parallel_vk)
        pop_topics_tg = get_popular_topics(processed_data_parallel_tg)

        with open('topics_vk.txt', 'a') as topics_vk:
            l = []
            for topic in pop_topics_vk:
                l.append(str(topic))
                topics_vk.write(str(topic) + '\n')
            self.vk = tk.Label(self, text='VK\n')
            self.vk.pack()
            self.vk_label = tk.Label(self, text='\n'.join(l))
            self.vk_label.pack()
        
        messagebox.showinfo("PREPROCESSED VK")

        with open('topics_tg.txt', 'a') as topics_tg:
            g = []
            for topic in pop_topics_tg:
                g.append(str(topic))
                topics_tg.write(str(topic) + '\n')
            self.tg = tk.Label(self, text='TG\n')
            self.tg.pack()
            self.tg_label = tk.Label(self, text='\n'.join(g))
            self.tg_label.pack()
        
        print("DONE")
        messagebox.showinfo('DONE')



if __name__ == '__main__':
    program_interface = ProgramInterface()
    program_interface.mainloop()



    











