from base.utils.cache import CacheProduct


class ConnectCache(object):
    def __init__(self, scene_id=None, mission_id=None):
        self.key = "%d_%d" % (int(scene_id), mission_id)
        self.connect_cache = CacheProduct("connect_cache")

    def set_frequency_cache(self, status="down"):
        """
        Increase the cache of mission check client number
        :return: the mission check client of number
        """
        connect_number = self.connect_cache.get(self.key, None)
        if status == "down":
            if connect_number is None:
                connect_number = 1
            else:
                connect_number = connect_number + 1
        else:
            connect_number = 0

        self.connect_cache.set(self.key, connect_number)
        return connect_number

    def blank_cache(self):
        """
        set the cache to 0
        :return: True
        """
        self.connect_cache.set(self.key, 0)
        return True
