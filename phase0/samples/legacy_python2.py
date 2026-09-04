# Legacy Python 2 code -- candidate migration target: Python 2 -> Python 3
import urllib2


class UserFetcher:
    def __init__(self, base_url):
        self.base_url = base_url
        self.cache = {}

    def fetch(self, user_id):
        if self.cache.has_key(user_id):
            return self.cache[user_id]

        url = self.base_url + "/users/" + str(user_id)
        response = urllib2.urlopen(url)
        data = response.read()
        print "Fetched user %s" % user_id

        self.cache[user_id] = data
        return data

    def fetch_many(self, user_ids):
        results = []
        for uid in user_ids:
            try:
                results.append(self.fetch(uid))
            except urllib2.URLError, e:
                print "Error fetching user:", e
        return results


if __name__ == '__main__':
    fetcher = UserFetcher("http://example.com/api")
    print fetcher.fetch_many([1, 2, 3])
