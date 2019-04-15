
from base.utils.enum import Enum


StatusUpdateEvent = Enum(
    SCENE_CREATE=1,
    SCENE_PAUSE=2,
    SCENE_RECOVER=3,
    SCENE_DELETE=4,
    SCENE_EXCEPT_DELETE=5,
)
