import os
import json
import re

BOOKMARKS_FILE = os.path.join(os.path.dirname(__file__), "data", "launcher_bookmarks.json")

def try_math(query):
    # Only allow digits, spaces, and math operators
    if not re.match(r'^[\d\.\s\+\-\*\/\(\)\%]+$', query):
        return None
    if not any(c in query for c in "+-*/%"):
        return None
    try:
        res = eval(query, {"__builtins__": None}, {})
        if isinstance(res, (int, float)):
            return res
    except Exception:
        return None

def quick_file_search(term):
    results = []
    term = term.lower()
    search_dirs = [os.path.expanduser("~"), os.path.expanduser("~/Downloads"), os.path.expanduser("~/Documents")]
    for d in search_dirs:
        try:
            for f in os.listdir(d):
                if term in f.lower():
                    results.append(os.path.join(d, f))
        except Exception:
            pass
    return results[:15]

def load_bookmarks():
    try:
        if not os.path.exists(BOOKMARKS_FILE):
            os.makedirs(os.path.dirname(BOOKMARKS_FILE), exist_ok=True)
            with open(BOOKMARKS_FILE, "w") as f:
                json.dump([], f)
            return []
            
        with open(BOOKMARKS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        pass
    return []

def toggle_bookmark(app_id):
    bookmarks = load_bookmarks()
    if app_id in bookmarks:
        bookmarks.remove(app_id)
    else:
        bookmarks.append(app_id)
    os.makedirs(os.path.dirname(BOOKMARKS_FILE), exist_ok=True)
    with open(BOOKMARKS_FILE, "w") as f:
        json.dump(bookmarks, f)

def get_app_id(item):
    if hasattr(item, "command_line"):
        return item.name
    if hasattr(item, "get_id"):
        return item.get_id()
    return getattr(item, 'display_name', '') or getattr(item, 'name', '')
