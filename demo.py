from Jikipedia import find_user, User, Entry


# 通过用户名检索用户
users = find_user("括弧")
for user in users:
    print(repr(user))
user = users[0]
user.query()
print(user)

# 查找用户词条
entries = user.fetch_entries()
for entry in entries:
    print(repr(entry))
entry = entries[0]
entry.query()
print(entry)

# 指定用户 id
user = User(824221130)
user.query()
print(user)

# 指定词条 id
entry = Entry(733278302)
entry.query()
print(entry)
