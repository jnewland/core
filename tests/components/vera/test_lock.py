"""Vera tests."""
from unittest.mock import MagicMock

import pyvera as pv

from homeassistant.const import (
    ATTR_CREDENTIALS,
    CONF_COMMAND_STATE,
    STATE_LOCKED,
    STATE_OK,
    STATE_UNLOCKED,
)
from homeassistant.core import HomeAssistant

from .common import ComponentFactory, new_simple_controller_config


async def test_lock(
    hass: HomeAssistant, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""
    vera_device: pv.VeraLock = MagicMock(spec=pv.VeraLock)
    vera_device.device_id = 1
    vera_device.vera_device_id = vera_device.device_id
    vera_device.comm_failure = False
    vera_device.name = "dev1"
    vera_device.category = pv.CATEGORY_LOCK
    vera_device.is_locked = MagicMock(return_value=False)
    vera_device.set_lock_pin = MagicMock(
        return_value=MagicMock(
            status_code=STATE_OK,
        )
    )
    vera_device.get_pin_codes = MagicMock(
        return_value=[[0, "test", "0123"], [1, "test2", "1234"]]
    )
    entity_id = "lock.dev1_1"

    component_data = await vera_component_factory.configure_component(
        hass=hass,
        controller_config=new_simple_controller_config(devices=(vera_device,)),
    )
    update_callback = component_data.controller_data[0].update_callback

    assert hass.states.get(entity_id).state == STATE_UNLOCKED

    await hass.services.async_call(
        "lock",
        "lock",
        {"entity_id": entity_id},
    )
    await hass.async_block_till_done()
    vera_device.lock.assert_called()
    vera_device.is_locked.return_value = True
    update_callback(vera_device)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_LOCKED

    await hass.services.async_call(
        "lock",
        "unlock",
        {"entity_id": entity_id},
    )
    await hass.async_block_till_done()
    vera_device.unlock.assert_called()
    vera_device.is_locked.return_value = False
    update_callback(vera_device)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNLOCKED

    assert "0123" in hass.states.get(entity_id).attributes[ATTR_CREDENTIALS]
    assert "1234" in hass.states.get(entity_id).attributes[ATTR_CREDENTIALS]

    await hass.services.async_call(
        "vera",
        "set_lock_pin",
        {"entity_id": entity_id, "name": "test3", "pin": "5678"},
    )
    await hass.async_block_till_done()
    vera_device.set_lock_pin.assert_called()
    assert hass.states.get(entity_id).attributes[CONF_COMMAND_STATE] == STATE_OK
