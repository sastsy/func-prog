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


if __name__ == '__main__':
    ray.init()
    print("STARTING")
    vk_result, tg_result = ray.get([parse_vk.remote(), parse_tg.remote()])
    result = vk_result + tg_result

    print("STARTED PREPROCESSING")

    processed_data_parallel = ray.get([parallel_preprocessing.remote(text) for text in result])
    
    pop_topics = get_popular_topics(processed_data_parallel)

    with open('topicss.txt', 'a') as topics:
        for topic in pop_topics:
            topics.write(str(topic) + '\n')
    
    print("DONE")



    











