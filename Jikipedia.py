from __future__ import annotations
from requests import Session

# from random import random
# from base64 import encodebytes


MAX_PAGE = 5
LOG = False


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
        assert data["id"] == self.user_id, "Unexpected error: ID mismatch!"
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
        self, include_anonymous: bool = False, max_page: int = MAX_PAGE, start: int = 1
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
                    "include_anonymous": include_anonymous,
                },
            )
            data = r.json()
            if LOG:
                print(f"[Fetch entries] Searching page #{data['current_page']}...")
            for entry_info in data["data"]:
                res.append(
                    Entry(
                        entry_info["id"],
                        entry_info["term"]["title"],
                        User(
                            entry_info["author"]["id"],
                            entry_info["author"]["name"],
                            entry_info["author"]["description"],
                        ),
                    )
                )
            if i >= data["last_page"]:
                if LOG:
                    print("[Fetch entries] No more results.")
                break
            if i >= max_page:
                if LOG:
                    print("[Fetch entries] Max pages limit reached!")
                break
            i += 1
        return res


class Entry:
    """词条"""

    def __init__(self, entry_id: int, title: str = None, author=None) -> None:
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
        self.author = author
        """磁珠"""
        self.likes = None
        """点赞数"""
        self.dislikes = None
        """点踩数"""
        self.anonymous = None
        """匿名发表"""
        self.raw_data = None
        """原始 json 数据"""

    def __str__(self) -> str:
        res = f"Title: {self.title}\n  Created: {self.created}\n  Updated: {self.updated}\n  Tags: {self.tags}\n  Author: {self.author.user_name}\n  Likes: {self.likes}\n  Dislikes: {self.dislikes}\n  Content:\n{self.content}"
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
        self.anonymous = data["anonymous"]
        self.raw_data = data
