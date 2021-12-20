import os
import re
from configparser import ConfigParser
from datetime import datetime
from random import randint, choice, shuffle, sample

import requests
from bs4 import BeautifulSoup


def loadConfig():
    if "config.ini" not in os.listdir("."):
        print("当前程序执行路径未找到配置文件config.ini\n程序退出")
        input("按下Enter键结束程序...")
        exit(0)
    config = ConfigParser()
    config.read(r"config.ini", encoding="utf-8")
    return config


def getKeywords(addr):
    try:
        if addr.startswith("http"):
            r = requests.get(addr)
            r.encoding = "utf-8"
            return [t.strip() for t in r.text.split("\n")]

        f = open(addr, encoding="utf-8")
        return [l.strip() for l in f.readlines()]
    except Exception as e:
        print(e)
        print("读取词库失败")


def getLinks(rt, d="", url=""):
    """
    :param rt: root 传入目录前面的绝对路径
    :param d: dir 传入要获取链接的目录
    :param url: 当用这个函数来获取图片链接的时候，在前面加url以更换链接
    :return: 获取到的所有链接
    """
    result = []
    path = os.path.join(rt, d)
    for root, dirs, files in os.walk(path):
        for file in files:
            if url:
                link = url + "/" + file
            else:
                bn = os.path.basename(root)
                # if len(bn) != 6 or not bn.startswith("2"):
                #     continue
                root = root.replace("\\", "/")
                link = root + "/" + file
            result.append(link.replace(rt, ""))
    return result


class RandomSite:
    def __init__(self):
        self.tags = ["a", "area", "audio", "b", "base", "basefont", "bdi", "bdo", "caption",
                     "code", "col", "colgroup", "datalist", "del", "dfn", "dialog",
                     "em", "embed", "font", "frame", "frameset", "ins", "kbd", "keygen",
                     "label", "link", "mark", "noframes", "output", "param", "picture",
                     "rp", "rt", "s", "samp", "small", "source", "strike",
                     "strong", "style", "sup", "tbody", "td", "tfoot", "th", "thead", "track",
                     "tt", "var",
                     ]
        self.attrs = ["class", "id", "dropzone", "date-time", "draggable", "dir", "title", "lang", "name"]
        self.seed = "1234567890abcdefghijklmnopqrstuvwxyz_"
        today = str(datetime.today())[2:10]
        self.dir = today[:2] + today[3:5] + today[6:]

        self.config = loadConfig()
        print("正在载入白词库...")
        self.whiteKeywords = getKeywords(self.config["通用"]["白词库"])
        print("正在载入灰词库...")
        self.grayKeywords = getKeywords(self.config["通用"]["灰词库"])
        print("正在载入尾词库...")
        self.tailKeywords = getKeywords(self.config["通用"]["尾词库"])
        print("正在载入文本库...")
        self.textBase = getKeywords(self.config["通用"]["文本库"])
        print("正在载入图片库...")
        self.picDir = self.config["通用"]["图库"]
        picUrl = self.config["通用"]["图库域名"]
        self.picLinks = getLinks(self.picDir, url=picUrl)
        self.tj = self.config["通用"]["统计代码"]
        self.script = self.config["通用"]["载入脚本"]

        self.curConf = None

        self.gens = {}
        for section in self.config.sections():
            if section.startswith("生成"):
                self.gens[section] = {}
                try:
                    self.gens[section]["siteName"] = self.config[section]["网站名"]
                    self.gens[section]["titleStyle"] = self.config[section]["标题格式"]
                    self.gens[section]["genCount"] = int(self.config[section]["生成数量"])
                    self.gens[section]["mainModel"] = self.config[section]["首页模板"]
                    self.gens[section]["typeModel"] = self.config[section]["分类页模板"]
                    self.gens[section]["detailModel"] = self.config[section]["详情页模板"]
                    self.gens[section]["playModel"] = self.config[section]["播放页模板"]

                    self.gens[section]["root"] = self.config[section]["网站根目录"]
                    self.gens[section]["typeDir"] = self.config[section]["分类页目录"]
                    self.gens[section]["detailDir"] = self.config[section]["详情页目录"]
                    self.gens[section]["playDir"] = self.config[section]["播放页目录"]

                    print("正在查找%s分类页链接..." % section)
                    self.gens[section]["typeLinks"] = getLinks(self.gens[section]["root"],
                                                               self.gens[section]["typeDir"])
                    print("正在查找%s详情页链接..." % section)
                    self.gens[section]["detailLinks"] = getLinks(self.gens[section]["root"],
                                                                 self.gens[section]["detailDir"])
                    print("正在查找%s播放页链接..." % section)
                    self.gens[section]["playLinks"] = getLinks(self.gens[section]["root"],
                                                               self.gens[section]["playDir"])
                except KeyError as e:
                    print(section, "缺少必要配置", e, "跳过此项")
                    self.gens.pop(section)

    def genTDK(self, mi=5, ma=10):
        wks = []
        gks = []
        for i in range(randint(mi, ma)):
            wks.append(choice(self.whiteKeywords)) if randint(0, 1) else gks.append(choice(self.grayKeywords))

        if not gks:
            gks.append(choice(self.grayKeywords))
        elif not wks:
            wks.append(choice(self.whiteKeywords))
        # print(gks)
        kws = []
        self.head = choice(wks)
        keywords = ",".join(kws)
        title = self.curConf["titleStyle"].replace("{hk}", choice(gks)).replace("{bk}", self.head).replace("{tk}",
                                                                                                           choice(
                                                                                                               self.tailKeywords))
        description = "%s是以%s为%s的%s网站，提供%s、%s、%s等视频，欢迎你前来免费观看" % \
                      (self.curConf["siteName"], choice(wks), choice(gks), choice(gks), choice(wks), choice(gks),
                       choice(wks))
        return title, description, keywords

    def changeHeader(self, head):
        t, d, k = self.genTDK()
        header = head.prettify()
        header = header.replace("{title}", t).replace("{description}", d).replace("{keywords}", k)
        return header

    def genIntro(self, length=150):
        intro = ""
        while True:
            if not randint(0, 2):
                intro += choice(self.grayKeywords)
            if len(intro) > length:
                return intro
            intro += choice(self.textBase)
            if not randint(0, 3):
                intro += choice(self.whiteKeywords)

    def changeLine(self, line, i="", genRandCode=True):
        """先用if判断是否有这个标签能大幅度提升效率"""
        if "{script}" in line:
            line = line.replace("{script}", self.script)
        if "{i}" in line:
            line = line.replace("{i}", i)
        if "{bk}" in line:
            line = line.replace("{bk}", choice(self.whiteKeywords))
        if "{hk}" in line:
            line = line.replace("{hk}", choice(self.grayKeywords))
        if "{dlink}" in line:
            line = line.replace("{dlink}", choice(self.curConf["detailLinks"]))
        if "{flink}" in line:
            line = line.replace("{flink}", choice(self.curConf["typeLinks"]))
        if "{plink}" in line:
            line = line.replace("{plink}", choice(self.curConf["playLinks"]))
        if "{pic}" in line:
            line = line.replace("{pic}", choice(self.picLinks))
        if "{tj}" in line:
            line = line.replace("{tj}", self.tj)
        if "{time}" in line or "{today}" in line or "{date}" in line or "{datetime}" in line:
            now = str(datetime.now())
            date = now[:10]
            today = now[5:10]
            time = now[11:16]
            dt = now[:16]
            line = line.replace("{date}", date).replace("{today}", today).replace("{time}", time).replace("{datetime}",
                                                                                                          dt)
        if "{intro}" in line:
            line = line.replace("{intro}", self.genIntro())
        if "{head}" in line:
            line = line.replace("{head}", self.head)
        if genRandCode and 'class="' in line:
            line = line.replace('class="', 'class="%s ' % self.randString())
        if "randint" in line:
            string = re.findall(r"\{.*?(randint.*?)\}", line)
            string = string[0].split(" ")
            if len(string[1:]) == 2:
                try:
                    line = re.sub(r"\{ *?randint.*?\}", str(randint(int(string[1]), int(string[2]))), line)
                except Exception as e:
                    print(e)

        return line

    def parseRandloop(self, plist, genRandCode):
        # 检索循环次数
        r = plist[0].strip()[1:-1].strip().split(" ")[1:]
        loopCount = randint(int(r[0]), int(r[1])) if len(r) == 2 else int(r[0])
        result = ""
        for i in range(loopCount):
            p = ""
            for l in plist[1:]:
                p += self.changeLine(l, str(i + 1), genRandCode)
            result += p

        # print(result)
        return result

    def randString(self, length=None):
        if length is None:
            length = randint(5, 7)
        return "".join(sample(self.seed, length))

    def genATag(self, attrCount=None):
        s = "<%s"
        tag = choice(self.tags)
        s %= tag
        attrCount = attrCount if attrCount else randint(0, 2)
        for _ in range(attrCount):
            s += ' %s="%s"' % (choice(self.attrs), self.randString())
        s += "></%s>" % tag
        return s

    def randTags(self, q=1):
        result = self.genATag()
        if q == 1:
            return result
        else:
            for _ in range(q - 1):
                tag = self.genATag()

                if randint(0, 3):  # 这里是嵌套概率，只有四分之一的概率不嵌套, 即使这样多层嵌套的概率也不大
                    t = result.split("><")
                    tag = tag[1:-1]
                    t.insert(randint(1, len(t) - 1), tag)
                    result = "><".join(t)
                else:
                    t = [result]
                    t.insert(randint(-1, 0), tag)
                    result = "".join(t)
            return result

    def changeBody(self, body, genRandCode):
        nbody = ""
        sp = re.compile(r"\{ *?(randloop.*?)\}")
        ep = re.compile(r"\{ *?/randloop.*?\}")
        loopPlist = []  # randint 段落
        loop = False  # 判断是否为randint 段落
        for line in str(body).split("\n"):
            if loop and re.findall(ep, line):  # 先匹配结束标签是因为正则会把结束标签也匹配成开始标签
                # 如果是结束标签就开始解析randint段落
                result = self.parseRandloop(loopPlist, genRandCode)

                nbody += result
                loopPlist.clear()
                loop = False
                continue
            elif re.findall(sp, line):
                # 判断是否开始了循环随随机次数段落
                loop = True

            if loop:
                # 如果是randint段落就添加到段落列表里面
                loopPlist.append(line)
                continue
            else:
                # 如果不是就直接处理行
                nbody += self.changeLine(line, genRandCode=genRandCode) + "\n"

                if genRandCode and not randint(0, 2):  # 三分之一的概率加一段没用的干扰代码
                    nbody += self.randTags(randint(2, 7))
        return nbody

    def genPage(self, model, genRandCode=True):
        htmlFile = open(model, encoding="utf-8")
        htmlDoc = htmlFile.read()
        bs = BeautifulSoup(htmlDoc, "html.parser")
        head = BeautifulSoup(self.changeHeader(bs.head), "html.parser")
        bs.head.replace_with(head)
        body = BeautifulSoup(self.changeBody(bs.body, genRandCode), "html.parser")
        # print(body)
        bs.body.replace_with(body)

        name = self.randString(6) + ".html"  # 重复率 0.001%
        tail = "/" + self.dir + "/" + name
        if model == self.curConf["typeModel"]:
            path = os.path.join(self.curConf["root"], self.curConf["typeDir"], self.dir, name)
            self.curConf["typeLinks"].append("/" + self.curConf["typeDir"] + tail)
        elif model == self.curConf["playModel"]:
            path = os.path.join(self.curConf["root"], self.curConf["playDir"], self.dir, name)
            self.curConf["playLinks"].append("/" + self.curConf["playDir"] + tail)
        elif model == self.curConf["detailModel"]:
            path = os.path.join(self.curConf["root"], self.curConf["detailDir"], self.dir, name)
            self.curConf["detailLinks"].append("/" + self.curConf["detailDir"] + tail)
        else:
            path = os.path.join(self.curConf["root"], "index.html")

        try:
            f = open(path, "w", encoding="utf-8")
        except Exception:
            os.makedirs(os.path.dirname(path))
            f = open(path, "w", encoding="utf-8")
        f.write(str(bs))
        f.close()

    def run(self):
        models = [self.curConf["playModel"], self.curConf["typeModel"], self.curConf["detailModel"]]

        for i in range(self.curConf["genCount"]):
            for m in models:
                self.genPage(m, )

    def __call__(self, *args, **kwargs):
        for k, v in self.gens.items():
            self.curConf = v
            self.run()
            self.genPage(v["mainModel"])
            print(k, "生成完毕")


if __name__ == '__main__':
    rs = RandomSite()
    rs()
