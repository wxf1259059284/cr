from cr_scene.models import CrEventScene, CrScene


def get_scene_by_id(scene_id, web=True):
    if web:
        cr_event = CrEventScene.objects.filter(cr_scene_instance=scene_id).first()
        if cr_event:
            return CrScene.objects.filter(id=cr_event.cr_scene_id).first()
            # return cr_event.cr_scene_instance
        return None

    return CrScene.objects.filter(scene_id=scene_id).first()
