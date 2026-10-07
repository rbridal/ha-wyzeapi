"""Camera poll without the clip list.

wyzeapy CameraService.update() always fetches the account event list before
reading power. Shop does not review clips in Home Assistant. This replaces
that method so a camera poll is the property read only.
"""

from __future__ import annotations

from typing import Any

from wyzeapy.services.base_service import BaseService
from wyzeapy.services.camera_service import DEVICEMGMT_API_MODELS, CameraService
from wyzeapy.types import PropertyIDs
from wyzeapy.services.camera_service import Camera


async def update_without_events(self: CameraService, camera: Camera) -> Camera:
    """Refresh one camera's power and toggles. Do not fetch clips."""
    async with BaseService._update_lock:
        camera.device_params = await self.get_updated_params(camera.mac)

    if camera.product_model in DEVICEMGMT_API_MODELS:
        state_response: dict[str, Any] = await self._get_iot_prop_devicemgmt(camera)
        for prop_category in state_response["data"]["capabilities"]:
            name = prop_category["name"]
            properties = prop_category["properties"]
            if name == "camera":
                camera.motion = properties["motion-detect-recording"]
            if name in ("floodlight", "spotlight"):
                camera.floodlight = properties["on"]
            if name == "siren":
                camera.siren = properties["state"]
            if name == "iot-device":
                camera.notify = properties["push-switch"]
                camera.on = properties["iot-power"]
                camera.available = properties["iot-state"]
        return camera

    state_response = await self._get_property_list(camera)
    for property_id, value in state_response:
        if property_id is PropertyIDs.AVAILABLE:
            camera.available = value == "1"
        elif property_id is PropertyIDs.ON:
            camera.on = value == "1"
        elif property_id is PropertyIDs.CAMERA_SIREN:
            camera.siren = value == "1"
        elif property_id is PropertyIDs.ACCESSORY:
            camera.floodlight = value == "1"
            if camera.device_params.get("dongle_product_model") == "HL_CGDC":
                camera.garage = value == "1"
        elif property_id is PropertyIDs.NOTIFICATION:
            camera.notify = value == "1"
        elif property_id is PropertyIDs.MOTION_DETECTION:
            camera.motion = value == "1"
    return camera


def install() -> None:
    """Replace the library camera update before any platform polls."""
    CameraService.update = update_without_events
