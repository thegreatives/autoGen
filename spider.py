from threading import Thread

import requests

resultKeywords = set([line.strip() for line in open("result_keywords.txt", encoding="utf-8").readlines()])
startKeywords = list(set([line.strip() for line in open("start_keywords.txt", encoding="utf-8").readlines()]))


def save():
    f = open("result_keywords.txt", "w", encoding="utf-8")
    for keyword in resultKeywords:
        f.write(keyword + "\n")

    f = open("start_keywords.txt", "w", encoding="utf-8")
    for keyword in startKeywords:
        try:
            f.write(keyword + "\n")
        except:
            continue


def parse(k):
    resultKeywords.add(k)
    url = "https://index.baidu.com/api/WordGraph/multi?wordlist[]=%s" % k
    try:
        temp = requests.get(url, timeout=10).json()
        wordGraph = temp["data"]["wordlist"][0]["wordGraph"]
    except Exception as e:
        print(k, e)
        save()
        return
    for i in wordGraph:
        print(i)
        resultKeywords.add(i["word"])
        if i not in startKeywords:
            startKeywords.append(i)


pool = []
for key in startKeywords:
    if type(key) == dict:
        continue

    t = Thread(target=parse, args=(key,))
    t.start()
    pool.append(t)

    if len(pool) > 8:
        for t in pool:
            t.join()
        pool.clear()
else:
    for t in pool:
        t.join()
    pool.clear()
    save()
