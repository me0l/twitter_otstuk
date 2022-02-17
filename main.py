import twint
from os import path
from threading import Thread
from re import compile

from telebot import TeleBot

from requests import head

find_urls = compile(r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b").findall


def get_tweets(target: str):
    c = twint.Config()
    c.Username = target
    c.Limit=100
    c.Store_object_tweets_list = []
    c.Store_object = True

    twint.run.Profile(c)
    
    return c.Store_object_tweets_list


def main_worker(target: str, access_token: str, user_id: int):
    scraped_tweets = get_tweets(target)
    bot = TeleBot(access_token)

    while True:
        tweets = get_tweets(target)
        current_tweet = tweets[0]

        filtered_tweets = list(filter(lambda tweet: tweet.id == current_tweet.id, scraped_tweets))
        
        if not len(filtered_tweets):
            scraped_tweets.append(current_tweet)
            text = current_tweet.tweet
            url_message = f"Все ссылки из твита - \n" + "\n".join(
                    map(
                        lambda resp: resp.headers["location"], 
                        map(head, find_urls(text))
                    )
                )

            bot.send_message(user_id, f"Новый твит от {target} - {current_tweet.quote_url}\n{current_tweet.tweet}")
            bot.send_message(user_id, url_message)
    

if __name__ == "__main__":
    if not path.isfile("telegram.txt"):
        access_token = input("Введите токен от телеграм бота(Напишите @botfather /newbot) -> ")
        user_id = int(input("Введите айди пользователя, кому нужно отправлять сообщение -> "))

        open("telegram.txt", "w+").write(f"{access_token};{str(user_id)}")
    else:
        access_token, user_id = open("telegram.txt", "r+").read().split(";")
        user_id = int(user_id)

    targets = open("twitters.txt", "r").read().strip().split("\n")

    for target in targets:
        task = Thread(target=main_worker, args=(target, access_token, user_id))
        task.start()
        task.join()
