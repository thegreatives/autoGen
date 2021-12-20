import requests
from bs4 import BeautifulSoup


def downloadImages(self):
    imgsFile = open(self.imgUrls, "r", encoding="utf-8")
    for url in imgsFile.readlines():
        url = url.strip()
        try:
            a = requests.get(url, timeout=30)
            print(url)
        except Exception as e:
            print(e)
            continue
        f = open(os.path.join(self.root, self.picDir, os.path.basename(url)), "wb")
        f.write(a.content)
        f.close()









def getImgUrls(url, savePath):
    host = url
    executedUrls = set()
    taskUrls = set()
    imgs = set()

    taskUrls.add(url)
    imgsFile = open(savePath, "a", encoding="utf-8")

    while True:
        try:
            url = taskUrls.pop()
        except TypeError:
            break

        try:
            print(url)
            res = requests.get(url)
            executedUrls.add(url)
        except Exception:
            continue

        bs = BeautifulSoup(res.text, "html.parser")
        for a in bs.find_all("a"):
            try:
                link = a["href"]
            except KeyError:
                continue

            if link.endswith("jpg") or link.endswith("gif") or link.endswith("png"):
                continue

            if link.startswith("/"):
                link = host + link
            elif host not in link:
                continue
            if link not in executedUrls:
                taskUrls.add(link)

        for img in bs.find_all("img"):
            try:
                pic = img["src"]
            except KeyError:
                continue

            if pic.startswith("//"):
                pic = "http:" + pic
            elif pic.startswith("/"):
                pic = host + pic

            if pic not in imgs:
                imgsFile.write(pic + "\n")
                imgs.add(pic)
