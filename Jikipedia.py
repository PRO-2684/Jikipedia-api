from __future__ import annotations
from requests import Session
from random import random
from time import sleep


MAX_PAGE = 5
LOG = False
MULTIPLIER = 5
SAVE_JSON = False  # 是否保存原始 json 数据


""" 失效
    https://api.jikipedia.com/wiki/request_search_placeholder # 搜索框热搜提示
    GET
    https://api.jikipedia.com/go/search_entities # 搜索 (综合)
    POST {"phrase":"依托答辩","page":1,"size":60}
    https://api.jikipedia.com/go/search_definitions # 搜索 (词条)
    POST {"phrase":"依托答辩","page":1,"size":60}
    https://api.jikipedia.com/go/search_albums # 搜索 (专辑)
    POST {"phrase":"依托答辩","page":1,"size":60}
    https://api.jikipedia.com/go/request_comments # 查询评论
    POST {"entity_id":198910808,"entity_category":"definition","comment_id":0,"page":1,"sort_by":"hot","full_context":false}
"""

""" 有效
    https://api.jikipedia.com/wiki/search_users # 搜索 (用户)
    POST {"phrase":"依托答辩","page":1,"size":60}
    https://api.jikipedia.com/go/request_user_public_info # 用户公开信息
    POST {"user_id":824221130}
    https://api.jikipedia.com/go/request_created_definition # 查询用户词条
    POST {"author_id":824221130,"page":1,"mode":"full","filter":"normal","sort_by":"hot","category":"normal","include_anonymous":false}
    https://api.jikipedia.com/go/request_definition # 词条内容
    POST {"id":198910808}
    https://api.jikipedia.com/go/list_user_configs # 用户配置 token needed ?
    POST {"user_id":824221130}
"""


def find_user(keyword: str, max_page: int = MAX_PAGE, start: int = 1) -> list[User]:
    """根据给定的 `keyword` 查找用户"""
    i = start
    res = []
    while True:
        r = x.post(
            "https://api.jikipedia.com/wiki/search_users",
            params={"phrase": keyword, "page": i, "size": 60},
        )
        data = r.json()
        if LOG:
            print(f"[Find user] Searching page #{data['current_page']}...")
        for user_info in data["data"]:
            res.append(
                User(user_info["id"], user_info["name"], user_info["description"])
            )
        if i >= data["last_page"]:
            if LOG:
                print("[Find user] No more results.")
            break
        if i >= max_page:
            if LOG:
                print("[Find user] Max pages limit reached!")
            break
        i += 1
    return res


def gen_xid() -> str:
    # 生成算法逆向不出来，但是抓到的 xid 貌似不会过期（）
    return "vRUFu93dvOFKGK4PehwZjUhZf5rhOgZ3IqIpByVfAhIb2qRZQlgjr61+OtdjDmYMMepqSrpItu9qX4daN7k/KQ5Q58wcQvS8MnaDOACn8uFuA3NZ3KSQ2oKX/USryVwX9FGe5J0UnZm2HjM+Ut8YtQ=="


x = Session()
x.headers.update(
    {
        "accept-encoding": "gzip",
        "client": "app",
        "client-version": "2.20.39",
        "content-type": "application/json; charset=utf-8",
        "host": "api.jikipedia.com",
        "xid": gen_xid(),
    }
)


class User:
    """用户"""

    def __init__(self, user_id: int, user_name=None, description=None) -> None:
        """根据给定的用户 id 实例化一个用户"""
        self.user_id = user_id
        """用户 id"""
        self.user_name = user_name
        """用户名"""
        self.description = description
        """个人简介"""
        self.avatar = None
        """头像链接"""
        self.background_image = None
        """背景图链接"""
        self.badge = None
        """佩戴的勋章"""
        self.likes = None
        """主页点赞数"""
        self.comments = None
        """留言数"""
        self.join_date = None
        """加入鸡窝的时间"""
        self.ip = None
        """IP 属地"""
        self.entry_count = None
        """词条数"""
        self.entry_likes = None
        """词条点赞数"""
        self.raw_data = None
        """原始 json 数据"""

    def __str__(self) -> str:
        res = f"Username: {self.user_name}\n  User id: {self.user_id}\n  Description: {self.description}\n  Avatar: {self.avatar}\n  Background image: {self.background_image}\n  Badge: {self.badge}\n  Likes: {self.likes}\n  Comments: {self.comments}\n  Join date: {self.join_date}\n  IP location: {self.ip}\n  Entry count: {self.entry_count}\n  Entry likes: {self.entry_likes}"
        return res

    def __repr__(self) -> str:
        return f'User(user_id={self.user_id}, user_name="{self.user_name}")'

    def query(self) -> None:
        """查询用户数据"""
        r = x.post(
            "https://api.jikipedia.com/go/request_user_public_info",
            json={"user_id": self.user_id},
        )
        data = r.json()
        assert data["id"] == self.user_id, f"Unexpected error: ID mismatch! {data}"
        self.user_name = data["name"]
        self.description = data["description"]
        self.avatar = data["avatar_detail"]["path"]
        self.background_image = data["background_image_detail"]["path"]
        self.badge = f'{data["badge"]["name"]}[{data["badge"]["title"]}]: {data["badge"]["description"]}'
        self.likes = data["like_count"]
        self.comments = data["comment_count"]
        self.join_date = data["created_at"]
        self.ip = (
            (data["ip_info"]["country"] + " - " + data["ip_info"]["province"])
            if data["ip_info"]["province"]
            else data["ip_info"]["country"]
        )
        self.entry_count = data["definition"]["create"]
        self.entry_likes = data["definition"]["like"]
        self.raw_data = data

    def fetch_entries(
        self, max_page: int = MAX_PAGE, start: int = 1, full: bool = False
    ) -> list[Entry]:
        """查询用户词条"""
        i = start
        res = []
        while True:
            r = x.post(
                "https://api.jikipedia.com/go/request_created_definition",
                json={
                    "author_id": self.user_id,
                    "page": i,
                    "mode": "full",
                    "filter": "normal",
                    "sort_by": "hot",
                    "category": "normal",
                    "include_anonymous": False,
                },
            )
            data = r.json()
            if LOG:
                print(f"[Fetch entries] Searching page #{data['current_page']}...")
            for entry_info in data["data"]:
                entry = Entry(
                    entry_info["id"],
                    entry_info["term"]["title"],
                    User(
                        entry_info["author"]["id"],
                        entry_info["author"]["name"],
                        entry_info["author"]["description"],
                    ),
                )
                if full:
                    entry.created = entry_info["created_at"]
                    entry.updated = entry_info["updated_at"]
                    entry.content = entry_info["content"]
                    entry.text = entry_info["plaintext"]
                    entry.tags = [tag["name"] for tag in entry_info["tags"]]
                    entry.likes = entry_info["like_count"]
                    entry.dislikes = entry_info["dislike_count"]
                    entry.shares = entry_info["share_count"]
                    entry.views = entry_info["view_count"]
                    entry.comments = entry_info["comment_count"]
                    entry.anonymous = entry_info["anonymous"]
                    entry.images = [
                        image["full"]["path"] for image in entry_info["images"]
                    ]
                    entry.raw_data = entry_info
                res.append(entry)
            if i >= data["last_page"]:
                if LOG:
                    print("[Fetch entries] No more results.")
                break
            if i >= max_page:
                if LOG:
                    print("[Fetch entries] Max pages limit reached!")
                break
            i += 1
            t = random() * MULTIPLIER
            print(f"暂停 {int(t)}s", end="\r")
            sleep(t)
        return res

    def fetch_miscs(
        self, max_page: int = MAX_PAGE, start: int = 1, full: bool = False
    ) -> list[Misc]:
        """查询用户杂谈"""
        i = start
        res = []
        while True:
            r = x.post(
                "https://api.jikipedia.com/go/request_created_definition",
                json={
                    "author_id": self.user_id,
                    "page": i,
                    "mode": "full",
                    "filter": "normal",
                    "sort_by": "hot",
                    "category": "post",
                    "include_anonymous": False,
                },
            )
            data = r.json()
            if LOG:
                print(f"[Fetch miscs] Searching page #{data['current_page']}...")
            for misc_info in data["data"]:
                misc = Misc(
                    misc_info["id"],
                    misc_info["plaintext"],
                    User(
                        misc_info["author"]["id"],
                        misc_info["author"]["name"],
                        misc_info["author"]["description"],
                    ),
                )
                if full:
                    misc.created = misc_info["created_at"]
                    misc.updated = misc_info["updated_at"]
                    misc.content = misc_info["content"]
                    misc.tags = [tag["name"] for tag in misc_info["tags"]]
                    misc.likes = misc_info["like_count"]
                    misc.dislikes = misc_info["dislike_count"]
                    misc.shares = misc_info["share_count"]
                    misc.views = misc_info["view_count"]
                    misc.comments = misc_info["comment_count"]
                    misc.anonymous = misc_info["anonymous"]
                    misc.images = [
                        image["full"]["path"] for image in misc_info["images"]
                    ]
                    misc.raw_data = misc_info
                res.append(misc)
            if i >= data["last_page"]:
                if LOG:
                    print("[Fetch miscs] No more results.")
                break
            if i >= max_page:
                if LOG:
                    print("[Fetch miscs] Max pages limit reached!")
                break
            i += 1
            t = random() * MULTIPLIER
            print(f"暂停 {int(t)}s", end="\r")
            sleep(t)
        return res


class Entry:
    """词条"""

    def __init__(self, entry_id: int, title: str = None, author: User = None) -> None:
        """根据给定词条 id 实例化一个词条"""
        self.entry_id = entry_id
        """词条 id"""
        self.created = None
        """创建时间"""
        self.updated = None
        """更新时间"""
        self.title = title
        """词条标题"""
        # self.term = None
        self.content = None
        """词条内容"""
        self.text = None
        """词条纯文本"""
        self.tags = []
        """词条标签"""
        # self.linked = []
        # self.references
        # self.videos
        self.author = author
        """磁珠"""
        self.likes = None
        """点赞数"""
        self.dislikes = None
        """点踩数"""
        self.shares = None
        """分享数"""
        self.views = None
        """查看数"""
        self.comments = None
        """评论数"""
        self.anonymous = None
        """匿名发表"""
        self.images = []
        """词条图片"""
        self.raw_data = None
        """原始 json 数据"""

    def __str__(self) -> str:
        res = f"Entry id: {self.entry_id}\n  Title: {self.title}\n  Created: {self.created}\n  Updated: {self.updated}\n  Author: {self.author.user_name}\n  Statistics: {self.likes} likes, {self.dislikes} dislikes, {self.shares} shares, {self.views} views, {self.comments} comments\n  Tags: {self.tags}\n  Images: {self.images}\n  Content:\n{self.content}"
        return res

    def __repr__(self) -> str:
        return f'Entry(entry_id={self.entry_id}, title="{self.title}")'

    def query(self) -> None:
        """查询词条详细信息"""
        r = x.post(
            "https://api.jikipedia.com/go/request_definition",
            json={"id": self.entry_id},
        )
        data = r.json()
        if data["category"] != "normal":
            raise RuntimeError("Error: " + data["category"])
        assert self.entry_id == data["id"]
        self.created = data["created_at"]
        self.updated = data["updated_at"]
        self.title = data["term"]["title"]
        # self.term = None # term_id: data["term"]["id"]
        self.content = data["content"]
        self.text = data["plaintext"]
        self.tags = [tag["name"] for tag in data["tags"]]
        # self.linked = []
        self.author = User(
            data["author"]["id"], data["author"]["name"], data["author"]["description"]
        )
        self.likes = data["like_count"]
        self.dislikes = data["dislike_count"]
        self.shares = data["share_count"]
        self.views = data["view_count"]
        self.comments = data["comment_count"]
        self.anonymous = data["anonymous"]
        self.images = [image["full"]["path"] for image in data["images"]]
        self.raw_data = data


class Misc:
    """杂谈"""

    def __init__(self, misc_id: int, text: str = None, author: User = None) -> None:
        """根据给定杂谈 id 实例化一个杂谈"""
        self.misc_id = misc_id
        """杂谈 id"""
        self.created = None
        """创建时间"""
        self.updated = None
        """更新时间"""
        self.content = None
        """杂谈描述"""
        self.text = text
        """杂谈纯文本"""
        self.tags = []
        """标签"""
        self.author = author
        """杂谈作者"""
        self.likes = None
        """点赞数"""
        self.dislikes = None
        """点踩数"""
        self.shares = None
        """分享数"""
        self.views = None
        """查看数"""
        self.comments = None
        """评论数"""
        self.anonymous = None
        """匿名发表"""
        self.images = []
        """杂谈图片"""
        self.raw_data = None
        """原始 json 数据"""

    def __str__(self) -> str:
        res = f"Misc id: {self.misc_id}\n  Created: {self.created}\n  Updated: {self.updated}\n  Author: {self.author.user_name}\n  Statistics: {self.likes} likes, {self.dislikes} dislikes, {self.shares} shares, {self.views} views, {self.comments} comments\n  Tags: {self.tags}\n  Images: {self.images}\n  Content:\n{self.content}"
        return res

    def __repr__(self) -> str:
        raw_text = self.text.replace("\n", "\\n")
        return f'Misc(misc_id={self.misc_id}, text="{raw_text}", author="{self.author.user_name}")'

    def query(self) -> None:
        """查询杂谈详细信息"""
        r = x.post(
            "https://api.jikipedia.com/go/request_definition",
            json={"id": self.misc_id},
        )
        data = r.json()
        if data["category"] != "post":
            raise RuntimeError("Error: " + data["category"])
        assert self.misc_id == data["id"]
        self.created = data["created_at"]
        self.updated = data["updated_at"]
        self.content = data["content"]
        self.text = data["plaintext"]
        self.tags = [tag["name"] for tag in data["tags"]]
        self.author = User(
            data["author"]["id"], data["author"]["name"], data["author"]["description"]
        )
        self.likes = data["like_count"]
        self.dislikes = data["dislike_count"]
        self.shares = data["share_count"]
        self.views = data["view_count"]
        self.comments = data["comment_count"]
        self.anonymous = data["anonymous"]
        self.images = [image["full"]["path"] for image in data["images"]]
        self.raw_data = data


if __name__ == "__main__":
    from os import mkdir
    from os.path import exists
    from json import dump

    def get_input(min_=1, max_=2) -> int:
        while True:
            s = input("> ")
            try:
                option = int(s)
            except:
                print("请输入十进制阿拉伯数字！")
            else:
                if min_ <= option <= max_:
                    print(f"你选择了项目 {option}")
                    return option
                else:
                    print(f"请输入大于等于 {min_} 小于等于 {max_} 的数字！")

    print("小鸡词典词条/杂谈备份工具 v1")
    while True:
        # 确定用户 id
        print("请选择一项: ")
        print("1. 我知道 id / 个人主页链接 (“APP - 我的 - 我的主页 - 右上角 - 分享 - 复制链接”)")
        print("2. 我只知道用户名")
        print("3. 我什么都不知道")
        option = get_input(1, 3)
        if option == 3:
            print("那我也无能为力了 :(")
            exit(0)
        elif option == 2:
            # TODO
            print("此项暂未完成")
            exit(0)
            username = input("请输入用户名: ")
            user_id = 0
        else:
            user_id = int(input("请输入你的 id（分享链接内位于“/user/”和“?”间的数字）: "))

        # 二次确认
        user = User(user_id=user_id)
        user.query()
        print("你是否想要备份以下用户的词条与杂谈: ")
        print(user)
        print("1. 是")
        print("2. 否")
        option = get_input()
        if option == 2:
            print("重新选择用户...")
            continue

        # TODO: 是否保存图片
        # print("你是否想要保存词条和杂谈的附加图片？")
        # print("1. 是")
        # print("2. 否")
        # option = get_input()
        # if option == 1:
        #     save_pic = True
        # else:
        #     save_pic = False

        # 备份词条
        print("正在备份词条...")
        dir_name = f"entries_{user.user_id}"
        if exists(dir_name):
            print("备份目录已存在，按下回车以继续（覆盖原文件），Ctrl+C 以取消")
            input()
        else:
            mkdir(dir_name)
        entries = user.fetch_entries(full=True)
        for entry in entries:
            print(f"备份《{entry.title}》...")
            with open(f"{dir_name}/{entry.entry_id}.txt", "w") as f:
                f.write(str(entry))
            if SAVE_JSON:
                with open(f"{dir_name}/{entry.entry_id}_raw.json", "w") as f:
                    raw = entry.raw_data
                    dump(raw, f)

        # 备份杂谈
        print("正在备份杂谈...")
        dir_name = f"miscs_{user.user_id}"
        if exists(dir_name):
            print("备份目录已存在，按下回车以继续（覆盖原文件），Ctrl+C 以取消")
            input()
        else:
            mkdir(dir_name)
        miscs = user.fetch_miscs(full=True)
        for misc in miscs:
            print(f"备份 #{misc.misc_id}...")
            with open(f"{dir_name}/{misc.misc_id}.txt", "w") as f:
                f.write(str(misc))
            if SAVE_JSON:
                with open(f"{dir_name}/{misc.misc_id}_raw.json", "w") as f:
                    raw = misc.raw_data
                    dump(raw, f)

        print("请选择一项: ")
        print("1. 退出")
        print("2. 继续备份其它用户的词条")
        option = get_input()
        if option == 1:
            break
